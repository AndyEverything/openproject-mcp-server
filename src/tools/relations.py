"""Work package relation management tools (follows, blocks, relates, etc.)."""

from typing import Optional
from pydantic import BaseModel, Field
from src.server import mcp, get_client
from src.utils.formatting import format_success, format_error


class CreateRelationInput(BaseModel):
    """Input model for creating work package relations."""
    from_id: int = Field(..., description="Source work package ID", gt=0)
    to_id: int = Field(..., description="Target work package ID", gt=0)
    type: str = Field(..., description="Relation type (relates, duplicates, blocks, precedes, follows, includes, requires, partof)")
    lag: Optional[int] = Field(None, description="Lag in working days (for precedes/follows)")
    description: Optional[str] = Field(None, description="Relation description")


class UpdateRelationInput(BaseModel):
    """Input model for updating work package relations."""
    relation_id: int = Field(..., description="Relation ID to update", gt=0)
    lag: Optional[int] = Field(None, description="New lag in working days")
    description: Optional[str] = Field(None, description="New description")


@mcp.tool
async def create_work_package_relation(input: CreateRelationInput) -> str:
    """Create a relation between two work packages.

    Relation types:
    - relates: General association
    - duplicates: Work package A duplicates B
    - blocks: Work package A blocks B
    - precedes: Work package A precedes B (A must finish before B starts)
    - follows: Work package A follows B (B must finish before A starts)
    - includes: Work package A includes B (part-of relationship)
    - requires: Work package A requires B
    - partof: Work package A is part of B

    Args:
        input: Relation data including from_id, to_id, type, and optional lag/description

    Returns:
        Success message with created relation details

    Example:
        {
            "from_id": 123,
            "to_id": 456,
            "type": "follows",
            "lag": 2,
            "description": "Wait 2 days after completion"
        }
    """
    try:
        client = get_client()

        data = {
            "from_id": input.from_id,
            "to_id": input.to_id,
            "type": input.type,
        }

        if input.lag is not None:
            data["lag"] = input.lag
        if input.description:
            data["description"] = input.description

        result = await client.create_work_package_relation(data)

        text = format_success(f"Relation created successfully!\n\n")
        text += f"**ID**: #{result.get('id', 'N/A')}\n"
        text += f"**Type**: {result.get('type', 'Unknown')}\n"

        embedded = result.get("_embedded", {})
        if "from" in embedded:
            text += f"**From**: {embedded['from'].get('subject', 'Unknown')} (#{input.from_id})\n"
        if "to" in embedded:
            text += f"**To**: {embedded['to'].get('subject', 'Unknown')} (#{input.to_id})\n"

        if result.get('lag'):
            text += f"**Lag**: {result['lag']} days\n"
        if result.get('description'):
            text += f"**Description**: {result['description']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to create relation: {str(e)}")


@mcp.tool
async def list_work_package_relations(work_package_id: int) -> str:
    """List all relations for a work package.

    Args:
        work_package_id: The work package ID

    Returns:
        List of all relations involving this work package
    """
    try:
        client = get_client()

        # Get relations for a specific work package
        import json
        filters = json.dumps([{"involved": {"operator": "=", "values": [str(work_package_id)]}}])
        result = await client.list_work_package_relations(filters)
        relations = result.get("_embedded", {}).get("elements", [])

        if not relations:
            return f"Work package #{work_package_id} has no relations."

        text = f"✅ **Relations for Work Package #{work_package_id} ({len(relations)}):**\n\n"
        for rel in relations:
            text += f"**Relation #{rel.get('id', 'N/A')}**\n"
            text += f"  Type: {rel.get('type', 'Unknown')}\n"

            embedded = rel.get("_embedded", {})
            if "from" in embedded:
                text += f"  From: {embedded['from'].get('subject', 'Unknown')} (#{embedded['from'].get('id', 'N/A')})\n"
            if "to" in embedded:
                text += f"  To: {embedded['to'].get('subject', 'Unknown')} (#{embedded['to'].get('id', 'N/A')})\n"

            if rel.get('lag'):
                text += f"  Lag: {rel['lag']} days\n"
            if rel.get('description'):
                text += f"  Description: {rel['description']}\n"

            text += "\n"

        return text

    except Exception as e:
        return format_error(f"Failed to list relations: {str(e)}")


@mcp.tool
async def get_work_package_relation(relation_id: int) -> str:
    """Get detailed information about a specific relation.

    Args:
        relation_id: The relation ID

    Returns:
        Detailed relation information
    """
    try:
        client = get_client()
        rel = await client.get_work_package_relation(relation_id)

        text = f"✅ **Relation #{rel.get('id')}**\n\n"
        text += f"**Type**: {rel.get('type', 'Unknown')}\n"

        embedded = rel.get("_embedded", {})
        if "from" in embedded:
            text += f"**From**: {embedded['from'].get('subject', 'Unknown')} (#{embedded['from'].get('id', 'N/A')})\n"
        if "to" in embedded:
            text += f"**To**: {embedded['to'].get('subject', 'Unknown')} (#{embedded['to'].get('id', 'N/A')})\n"

        if rel.get('lag'):
            text += f"**Lag**: {rel['lag']} days\n"
        if rel.get('description'):
            text += f"**Description**: {rel['description']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to get relation: {str(e)}")


@mcp.tool
async def update_work_package_relation(input: UpdateRelationInput) -> str:
    """Update a work package relation (modify lag or description).

    Args:
        input: Relation update data including relation_id and fields to update

    Returns:
        Success message with updated relation details
    """
    try:
        client = get_client()

        update_data = {}

        if input.lag is not None:
            update_data["lag"] = input.lag
        if input.description is not None:
            update_data["description"] = input.description

        if not update_data:
            return format_error("No fields provided to update")

        result = await client.update_work_package_relation(input.relation_id, update_data)

        text = format_success(f"Relation #{input.relation_id} updated successfully!\n\n")
        text += f"**Type**: {result.get('type', 'Unknown')}\n"

        if result.get('lag'):
            text += f"**Lag**: {result['lag']} days\n"
        if result.get('description'):
            text += f"**Description**: {result['description']}\n"

        return text

    except Exception as e:
        return format_error(f"Failed to update relation: {str(e)}")


@mcp.tool
async def delete_work_package_relation(relation_id: int) -> str:
    """Delete a work package relation.

    Args:
        relation_id: ID of the relation to delete

    Returns:
        Success or error message
    """
    try:
        client = get_client()

        success = await client.delete_work_package_relation(relation_id)

        if success:
            return format_success(f"Relation #{relation_id} deleted successfully")
        else:
            return format_error(f"Failed to delete relation #{relation_id}")

    except Exception as e:
        return format_error(f"Failed to delete relation: {str(e)}")
