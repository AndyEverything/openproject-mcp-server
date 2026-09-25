"""Tests for OpenProjectClient HTTP layer (aioresponses, no network)."""

import asyncio
import json
import mimetypes
import re

import pytest
from aioresponses import aioresponses

from src.client import (
    DownloadTooLargeError,
    OpenProjectAPIError,
    OpenProjectClient,
)
from src.utils.cache import TTLCache

BASE = "https://op.example.test"
API = f"{BASE}/api/v3"
ANY_URL = re.compile(r".*")


@pytest.fixture
def client():
    c = OpenProjectClient(base_url=BASE, api_key="secret")
    c.cache = TTLCache(ttl=0)
    return c


@pytest.fixture
def http():
    with aioresponses() as m:
        yield m


def sent_requests(m):
    """Flatten aioresponses.requests into [(method, URL, kwargs)] in call order."""
    calls = []
    for (method, url), items in m.requests.items():
        for call in items:
            calls.append((method, url, call.kwargs))
    return calls


def only_request(m):
    calls = sent_requests(m)
    assert len(calls) == 1, calls
    return calls[0]


# --- 2.1 OpenProjectAPIError -------------------------------------------------


async def test_request_404_raises_typed_error_with_legacy_message(client, http):
    http.get(f"{API}/work_packages/999", status=404, body='{"message":"nope"}')

    with pytest.raises(OpenProjectAPIError) as exc_info:
        await client.get_work_package(999)

    error = exc_info.value
    assert error.status == 404
    assert error.body == '{"message":"nope"}'
    assert str(error) == (
        'API Error 404: {"message":"nope"}\n\n'
        "Resource not found. Please verify the URL and resource exists."
    )
    assert isinstance(error, Exception)


async def test_request_error_without_hint_keeps_plain_message(client, http):
    http.get(f"{API}/statuses", status=422, body="invalid")

    with pytest.raises(OpenProjectAPIError) as exc_info:
        await client.get_statuses()

    assert str(exc_info.value) == "API Error 422: invalid"
    assert exc_info.value.status == 422


# --- 2.2 _request_bytes -------------------------------------------------------


async def test_request_bytes_returns_content_type_and_filename(client, http):
    http.get(
        f"{API}/attachments/7/content",
        body=b"\x89PNG-data",
        content_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="zrzut ekranu.png"'},
    )

    content, content_type, filename = await client.download_attachment(7)

    assert content == b"\x89PNG-data"
    assert content_type == "image/png"
    assert filename == "zrzut ekranu.png"
    _, _, kwargs = only_request(http)
    assert kwargs["headers"]["Accept"] == "*/*"
    assert "Authorization" in kwargs["headers"]
    assert "Content-Type" not in kwargs["headers"]
    assert kwargs["allow_redirects"] is False


async def test_request_bytes_without_content_disposition_gives_none_filename(client, http):
    http.get(f"{API}/attachments/8/content", body=b"abc", content_type="text/plain")

    _, _, filename = await client.download_attachment(8)

    assert filename is None


async def test_request_bytes_redirect_to_other_host_drops_authorization(client, http):
    presigned = "https://s3.storage.test/bucket/file.png?X-Amz-Signature=abc"
    http.get(
        f"{API}/attachments/7/content", status=302, headers={"Location": presigned}
    )
    http.get(presigned, body=b"img", content_type="image/png")

    content, _, _ = await client.download_attachment(7)

    assert content == b"img"
    first, second = sent_requests(http)
    assert first[1].host == "op.example.test"
    assert "Authorization" in first[2]["headers"]
    assert second[1].host == "s3.storage.test"
    assert "Authorization" not in second[2]["headers"]


async def test_request_bytes_relative_redirect_keeps_authorization(client, http):
    http.get(
        f"{API}/attachments/7/content",
        status=307,
        headers={"Location": "/files/7/download"},
    )
    http.get(f"{BASE}/files/7/download", body=b"ok", content_type="text/plain")

    content, _, _ = await client.download_attachment(7)

    assert content == b"ok"
    _, second = sent_requests(http)
    assert str(second[1]) == f"{BASE}/files/7/download"
    assert "Authorization" in second[2]["headers"]


async def test_request_bytes_too_many_redirects(client, http):
    http.get(
        ANY_URL, status=302, headers={"Location": f"{BASE}/loop"}, repeat=True
    )

    with pytest.raises(Exception, match="Too many redirects"):
        await client.download_attachment(7)

    assert len(sent_requests(http)) == 4


async def test_request_bytes_exceeding_limit_raises_readable_error(client, http):
    http.get(f"{API}/attachments/7/content", body=b"x" * 11, content_type="image/png")

    with pytest.raises(DownloadTooLargeError, match="size limit of 10 bytes"):
        await client._request_bytes("/attachments/7/content", max_bytes=10)


async def test_request_bytes_error_status_raises_api_error(client, http):
    http.get(f"{API}/attachments/7/content", status=403, body="forbidden")

    with pytest.raises(OpenProjectAPIError) as exc_info:
        await client.download_attachment(7)

    assert exc_info.value.status == 403


async def test_request_bytes_accepts_api_href(client, http):
    http.get(f"{API}/attachments/9/content", body=b"z", content_type="text/plain")

    content, _, _ = await client._request_bytes("/api/v3/attachments/9/content")

    assert content == b"z"


# --- 2.3 _request_multipart -----------------------------------------------------


async def test_upload_attachment_sends_metadata_and_file_parts(client, http, tmp_path):
    file_path = tmp_path / "raport.csv"
    file_path.write_bytes(b"a;b\n1;2\n")
    http.post(
        f"{API}/work_packages/12/attachments",
        status=201,
        payload={"id": 555, "fileName": "raport.csv"},
    )

    result = await client.upload_attachment(12, str(file_path), description="Opis pliku")

    assert result["id"] == 555
    method, _, kwargs = only_request(http)
    assert method == "POST"
    assert "Content-Type" not in kwargs["headers"]
    assert "Authorization" in kwargs["headers"]

    parts = {
        options["name"]: (options, headers, value)
        for options, headers, value in kwargs["data"]._fields
    }
    meta_options, meta_headers, meta_value = parts["metadata"]
    assert meta_headers["Content-Type"] == "application/json"
    assert json.loads(meta_value) == {
        "fileName": "raport.csv",
        "description": {"raw": "Opis pliku"},
    }
    file_options, file_headers, file_value = parts["file"]
    assert file_options["filename"] == "raport.csv"
    # MIME wg mimetypes (na Windows zależy od rejestru)
    assert file_headers["Content-Type"] == mimetypes.guess_type("raport.csv")[0]
    assert file_value == b"a;b\n1;2\n"


async def test_upload_attachment_without_description_and_unknown_type(client, http, tmp_path):
    file_path = tmp_path / "dane.unknownext"
    file_path.write_bytes(b"\x00\x01")
    http.post(f"{API}/work_packages/12/attachments", status=201, payload={"id": 1})

    await client.upload_attachment(12, str(file_path))

    _, _, kwargs = only_request(http)
    parts = {o["name"]: (o, h, v) for o, h, v in kwargs["data"]._fields}
    assert json.loads(parts["metadata"][2]) == {"fileName": "dane.unknownext"}
    assert parts["file"][1]["Content-Type"] == "application/octet-stream"


async def test_multipart_error_raises_api_error(client, http, tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("x")
    http.post(f"{API}/work_packages/12/attachments", status=422, body="too big")

    with pytest.raises(OpenProjectAPIError) as exc_info:
        await client.upload_attachment(12, str(file_path))

    assert exc_info.value.status == 422


# --- 2.4 new client methods -----------------------------------------------------

METHOD_CASES = [
    pytest.param(
        lambda c: c.get_current_user(), "GET", "/users/me", {}, None, id="current_user"
    ),
    pytest.param(
        lambda c: c.get_work_package_schema(118, 7),
        "GET", "/work_packages/schemas/118-7", {}, None, id="schema",
    ),
    pytest.param(
        lambda c: c.get_work_package_attachments(5),
        "GET", "/work_packages/5/attachments", {}, None, id="wp_attachments",
    ),
    pytest.param(
        lambda c: c.get_attachment(42), "GET", "/attachments/42", {}, None, id="attachment"
    ),
    pytest.param(
        lambda c: c.get_work_package_form(5, 15),
        "POST", "/work_packages/5/form", {}, {"lockVersion": 15}, id="form",
    ),
    pytest.param(
        lambda c: c.get_watchers(5), "GET", "/work_packages/5/watchers", {}, None, id="watchers"
    ),
    pytest.param(
        lambda c: c.add_watcher(5, 304),
        "POST", "/work_packages/5/watchers", {},
        {"user": {"href": "/api/v3/users/304"}}, id="add_watcher",
    ),
    pytest.param(
        lambda c: c.remove_watcher(5, 304),
        "DELETE", "/work_packages/5/watchers/304", {}, None, id="remove_watcher",
    ),
    pytest.param(lambda c: c.get_queries(), "GET", "/queries", {}, None, id="queries"),
    pytest.param(
        lambda c: c.get_queries(project_id=118),
        "GET", "/queries",
        {"filters": [{"project": {"operator": "=", "values": ["118"]}}]},
        None, id="queries_project",
    ),
    pytest.param(
        lambda c: c.get_query(77),
        "GET", "/queries/77", {"offset": "1", "pageSize": "20"}, None, id="query",
    ),
    pytest.param(
        lambda c: c.get_query(77, offset=3, page_size=50),
        "GET", "/queries/77", {"offset": "3", "pageSize": "50"}, None, id="query_paging",
    ),
    pytest.param(
        lambda c: c.get_notifications(),
        "GET", "/notifications",
        {
            "filters": [{"readIAN": {"operator": "=", "values": ["f"]}}],
            "offset": "1",
            "pageSize": "20",
        },
        None, id="notifications_default",
    ),
    pytest.param(
        lambda c: c.get_notifications(reason="mentioned", offset=2, page_size=10),
        "GET", "/notifications",
        {
            "filters": [
                {"readIAN": {"operator": "=", "values": ["f"]}},
                {"reason": {"operator": "=", "values": ["mentioned"]}},
            ],
            "offset": "2",
            "pageSize": "10",
        },
        None, id="notifications_reason",
    ),
    pytest.param(
        lambda c: c.get_notifications(unread_only=False),
        "GET", "/notifications", {"offset": "1", "pageSize": "20"}, None,
        id="notifications_all",
    ),
    pytest.param(lambda c: c.get_version(9), "GET", "/versions/9", {}, None, id="version"),
    pytest.param(
        lambda c: c.update_version(9, {"status": "closed"}),
        "PATCH", "/versions/9", {}, {"status": "closed"}, id="update_version",
    ),
    pytest.param(
        lambda c: c.get_work_package_link_collection(5, "github_pull_requests"),
        "GET", "/work_packages/5/github_pull_requests", {}, None, id="link_collection",
    ),
]


@pytest.mark.parametrize("call, method, path, query, body", METHOD_CASES)
async def test_client_methods_build_expected_requests(client, http, call, method, path, query, body):
    http.add(ANY_URL, method=method, payload={"_type": "Collection"})

    await call(client)

    sent_method, url, kwargs = only_request(http)
    assert sent_method == method
    assert url.path == f"/api/v3{path}"
    actual_query = {
        key: json.loads(value) if key == "filters" else value
        for key, value in url.query.items()
    }
    assert actual_query == query
    assert kwargs.get("json") == body


async def test_collection_methods_guarantee_elements(client, http):
    http.get(f"{API}/work_packages/5/watchers", payload={"_type": "Collection"})

    result = await client.get_watchers(5)

    assert result["_embedded"]["elements"] == []


# --- 3.1 cache wiring ------------------------------------------------------------


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def request_count(m):
    return len(sent_requests(m))


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def cached_client(clock):
    c = OpenProjectClient(base_url=BASE, api_key="secret")
    c.cache = TTLCache(ttl=600, clock=clock)
    return c


STATUSES = {"_embedded": {"elements": [{"id": 1, "name": "Nowy"}]}}


@pytest.mark.parametrize(
    "call, path",
    [
        (lambda c: c.get_statuses(), "/statuses"),
        (lambda c: c.get_priorities(), "/priorities"),
        (lambda c: c.get_types(), "/types"),
        (lambda c: c.get_types(118), "/projects/118/types"),
        (lambda c: c.get_work_package_schema(118, 7), "/work_packages/schemas/118-7"),
        (lambda c: c.get_current_user(), "/users/me"),
    ],
)
async def test_cached_methods_hit_api_once_within_ttl(cached_client, http, call, path):
    http.get(f"{API}{path}", payload=STATUSES, repeat=True)

    first = await call(cached_client)
    second = await call(cached_client)

    assert first == second
    assert request_count(http) == 1


async def test_types_cache_is_keyed_by_project(cached_client, http):
    http.get(f"{API}/types", payload=STATUSES, repeat=True)
    http.get(f"{API}/projects/118/types", payload=STATUSES, repeat=True)

    await cached_client.get_types()
    await cached_client.get_types(118)

    assert request_count(http) == 2


async def test_concurrent_reads_share_one_request(cached_client, http):
    http.get(f"{API}/statuses", payload=STATUSES, repeat=True)

    results = await asyncio.gather(
        cached_client.get_statuses(), cached_client.get_statuses()
    )

    assert results[0] == results[1]
    assert request_count(http) == 1


async def test_expired_entry_triggers_new_request(cached_client, http, clock):
    http.get(f"{API}/statuses", payload=STATUSES, repeat=True)

    await cached_client.get_statuses()
    clock.now += 601
    await cached_client.get_statuses()

    assert request_count(http) == 2


async def test_ttl_zero_disables_cache(client, http):
    http.get(f"{API}/statuses", payload=STATUSES, repeat=True)

    await client.get_statuses()
    await client.get_statuses()

    assert request_count(http) == 2


async def test_cached_result_mutation_does_not_leak(cached_client, http):
    http.get(f"{API}/statuses", payload=STATUSES, repeat=True)

    first = await cached_client.get_statuses()
    first["_embedded"]["elements"].clear()
    second = await cached_client.get_statuses()

    assert second["_embedded"]["elements"] == [{"id": 1, "name": "Nowy"}]
