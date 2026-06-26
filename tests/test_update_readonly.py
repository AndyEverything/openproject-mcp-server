"""Unit coverage for update_work_package's read-only percentage_done handling.

On some OpenProject instances percentage_done is read-only and the API rejects it
with HTTP 422 PropertyIsReadOnly. The tool should drop that field and retry so the
rest of the update still applies, without swallowing unrelated errors. These tests
mock the client, so they are network-free.
"""

from src.tools import work_packages as wp


class _FakeClient:
    def __init__(self):
        self.calls = []

    async def update_work_package(self, wp_id, data):
        self.calls.append(dict(data))
        if "percentage_done" in data:
            raise Exception(
                "API Error 422: PropertyIsReadOnly - "
                "Percentage done was attempted to be written but is not writable."
            )
        return {"id": wp_id, "subject": "S", "_embedded": {}}


async def test_percentage_readonly_retries_without_field(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(wp, "get_client", lambda: fake)

    result = await wp.update_work_package.fn(
        work_package_id=1, status_id=2, percentage_done=50
    )

    assert "updated successfully" in result.lower()
    assert "percentage_done is read-only" in result
    # First attempt included the field; retry dropped it but kept status_id.
    assert len(fake.calls) == 2
    assert "percentage_done" in fake.calls[0]
    assert "percentage_done" not in fake.calls[1]
    assert fake.calls[1]["status_id"] == 2


async def test_percentage_readonly_only_field_returns_clear_message(monkeypatch):
    fake = _FakeClient()
    monkeypatch.setattr(wp, "get_client", lambda: fake)

    result = await wp.update_work_package.fn(work_package_id=1, percentage_done=50)

    assert "read-only" in result.lower()
    assert "no other fields" in result.lower()
    assert len(fake.calls) == 1  # no pointless retry with an empty payload


async def test_non_readonly_error_is_not_swallowed(monkeypatch):
    class _BoomClient:
        async def update_work_package(self, wp_id, data):
            raise Exception("API Error 404: not found")

    monkeypatch.setattr(wp, "get_client", lambda: _BoomClient())

    result = await wp.update_work_package.fn(
        work_package_id=1, status_id=2, percentage_done=50
    )

    assert "failed to update" in result.lower()


async def test_percentage_readonly_detected_via_identifier_when_localized(monkeypatch):
    # Even with a translated/reworded human message, detection must still fire off
    # the stable v3 errorIdentifier + attribute name in the 422 body.
    class _LocalizedClient:
        def __init__(self):
            self.calls = []

        async def update_work_package(self, wp_id, data):
            self.calls.append(dict(data))
            if "percentage_done" in data:
                raise Exception(
                    'API Error 422: {"_type":"Error","errorIdentifier":'
                    '"urn:openproject-org:api:v3:errors:PropertyIsReadOnly",'
                    '"message":"Fertigstellungsgrad ist schreibgeschuetzt.",'
                    '"_embedded":{"details":{"attribute":"percentageDone"}}}'
                )
            return {"id": wp_id, "subject": "S", "_embedded": {}}

    fake = _LocalizedClient()
    monkeypatch.setattr(wp, "get_client", lambda: fake)

    result = await wp.update_work_package.fn(
        work_package_id=1, status_id=2, percentage_done=50
    )

    assert "updated successfully" in result.lower()
    assert len(fake.calls) == 2
    assert "percentage_done" not in fake.calls[1]
