"""Work package hierarchy management tools (parent-child relationships)."""

from typing import Optional
from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error, format_work_package_list


@mcp.tool
async def set_work_package_parent(child_id: int, parent_id: int) -> str:
    """Set a work package as child of another (create parent-child relationship).

    Args:
        child_id: ID of the child work package
        parent_id: ID of the parent work package

    Returns:
        Success message confirming the relationship
    """
    try:
        client = get_client()

        # Update child to set parent
        data = {"parent_id": parent_id}
        result = await client.update_work_package(child_id, data)

        text = format_success(f"Work package #{child_id} is now child of #{parent_id}\n\n")
        text += f"**Child**: {result.get('subject', 'Unknown')}\n"

        embedded = result.get("_embedded", {})
        if "parent" in embedded:
            text += f"**Parent**: {embedded['parent'].get('subject', 'Unknown')}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to set parent: {str(e)}")


@mcp.tool
async def remove_work_package_parent(work_package_id: int) -> str:
    """Remove parent from a work package (break parent-child relationship).

    Args:
        work_package_id: ID of the work package to remove parent from

    Returns:
        Success message
    """
    try:
        client = get_client()

        # Update to remove parent (set to null)
        data = {"parent_id": None}
        result = await client.update_work_package(work_package_id, data)

        return format_success(f"Removed parent from work package #{work_package_id}")

    except Exception as e:
        return format_error(f"Failed to remove parent: {str(e)}")


@mcp.tool
async def list_work_package_children(
    work_package_id: int,
    offset: int = 0,
    page_size: int = 20
) -> str:
    """List all children of a work package.

    Args:
        work_package_id: ID of the parent work package
        offset: Starting index for pagination (default: 0)
        page_size: Number of results per page (default: 20, max: 100)

    Returns:
        List of child work packages
    """
    try:
        client = get_client()

        result = await client.get_work_package_children(
            parent_id=work_package_id,
            offset=offset,
            page_size=page_size
        )

        children = result.get("_embedded", {}).get("elements", [])
        total = result.get("total", len(children))

        if not children:
            return f"Work package #{work_package_id} has no children."

        text = f"✅ **Children of Work Package #{work_package_id}:**\n\n"
        text += format_work_package_list(children)

        # Add pagination info
        if total > page_size:
            text += f"\n📄 **Pagination**: Showing {offset + 1}-{offset + len(children)} of {total} total\n"
            text += f"   Use `offset={offset + page_size}` to see next page\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list children: {str(e)}")


def _wp_id_from_href(href: Optional[str]) -> Optional[int]:
    """Extract the work package id from an API href like /api/v3/work_packages/616."""
    if not href:
        return None
    tail = href.rstrip("/").split("/")[-1]
    return int(tail) if tail.isdigit() else None


def _wp_status(wp: dict) -> tuple:
    """Return (status name, is_closed) from an embedded work package."""
    st = (wp.get("_embedded") or {}).get("status") or {}
    name = st.get("name") or (wp.get("_links", {}).get("status") or {}).get("title", "?")
    return name, bool(st.get("isClosed", name == "Closed"))


@mcp.tool
async def get_work_package_tree(work_package_id: int, max_depth: int = 4) -> str:
    """Show a work package's ancestors and all descendants as a tree, with status and rollup.

    Use it to see epic progress at a glance (e.g. how many children of #641 are
    Closed) without fetching each child. Read-only.

    Args:
        work_package_id: ID of the work package to centre the tree on
        max_depth: How many levels of descendants to show (default 4, max 10)

    Returns:
        Ancestor chain, then the descendant tree (id, subject, status) and a
        closed/total count for the whole subtree
    """
    try:
        client = get_client()
        max_depth = max(1, min(max_depth, 10))

        root = await client.get_work_package(work_package_id)

        # Ancestors: walk parent links upward (guard against cycles/deep chains)
        ancestors, seen, cur = [], {work_package_id}, root
        while len(ancestors) < 10:
            pid = _wp_id_from_href((cur.get("_links", {}).get("parent") or {}).get("href"))
            if not pid or pid in seen:
                break
            seen.add(pid)
            cur = await client.get_work_package(pid)
            ancestors.append(cur)
        ancestors.reverse()

        # Descendants: OpenProject 13 has no descendants/ancestor filter, so walk
        # the subtree level by level; the parent filter accepts many ids at once.
        import json
        from urllib.parse import quote
        elements, frontier, depth_seen = [], [work_package_id], 0
        while frontier and depth_seen < 10 and len(elements) < 1000:
            depth_seen += 1
            level, offset = [], 0
            filters = json.dumps([{"parent": {"operator": "=", "values": [str(i) for i in frontier]}}])
            while True:
                page = await client._request(
                    "GET",
                    f"/work_packages?pageSize=100&offset={offset}&filters={quote(filters)}",
                )
                batch = page.get("_embedded", {}).get("elements", [])
                level.extend(batch)
                offset += len(batch)
                if not batch or offset >= page.get("total", 0):
                    break
            elements.extend(level)
            frontier = [wp["id"] for wp in level]
        total = len(elements)

        by_parent = {}
        for wp in elements:
            pid = _wp_id_from_href((wp.get("_links", {}).get("parent") or {}).get("href"))
            by_parent.setdefault(pid, []).append(wp)
        for kids in by_parent.values():
            kids.sort(key=lambda w: w.get("id", 0))

        nl = chr(10)
        lines = []
        for depth, a in enumerate(ancestors):
            lines.append(f"{'  ' * depth}↑ #{a['id']} {a.get('subject', '')} [{_wp_status(a)[0]}]")
        base = len(ancestors)
        rname = _wp_status(root)[0]
        lines.append(f"{'  ' * base}● #{root['id']} {root.get('subject', '')} [{rname}]")

        def walk(pid, depth):
            for wp in by_parent.get(pid, []):
                if depth > max_depth:
                    continue
                name, _ = _wp_status(wp)
                n_desc = len(by_parent.get(wp["id"], []))
                more = f" (+{n_desc} hidden, depth limit)" if depth == max_depth and n_desc else ""
                lines.append(f"{'  ' * (base + depth)}- #{wp['id']} {wp.get('subject', '')} [{name}]{more}")
                walk(wp["id"], depth + 1)

        walk(work_package_id, 1)

        closed = sum(1 for wp in elements if _wp_status(wp)[1])
        direct = by_parent.get(work_package_id, [])
        direct_closed = sum(1 for wp in direct if _wp_status(wp)[1])
        lines.append("")
        lines.append(f"Descendants: {closed}/{len(elements)} closed. Direct children: {direct_closed}/{len(direct)} closed.")
        if len(elements) < total:
            lines.append(f"Note: only {len(elements)} of {total} descendants loaded (cap reached).")
        return nl.join(lines)

    except Exception as e:
        return format_error(f"Failed to build tree for #{work_package_id}: {str(e)}")
