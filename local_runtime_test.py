from __future__ import annotations

import asyncio
import os

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import CreateMessageResult, TextContent

MCP_URL = os.environ.get("MCP_URL", "http://localhost:8000/mcp")

RESPONSES = iter(
    [
        {"topic": "Weekly Product Sync"},
        {"participants": "Alex, Sam, Jordan"},
        {"meeting_date": "2026-04-22"},
        {"duration_minutes": 45},
        {"confirm": "yes"},
    ]
)


async def elicitation_handler(message, response_type, params, context):
    response = next(RESPONSES)
    print(f"Server asks: {message}")
    print(f"Client responds: {response}\n")
    return response


async def sampling_handler(messages, params, context):
    print("Sampling request received\n")
    generated_text = """Subject: Weekly Product Sync

Hi team, I scheduled this session so we can align on current priorities, unblock open decisions, and confirm the next delivery steps.

Agenda:
- Review progress since the last sync
- Resolve open product and delivery decisions
- Confirm owners and next milestones

Please come with any blockers or dependencies you want to surface."""
    return CreateMessageResult(
        role="assistant",
        content=TextContent(type="text", text=generated_text),
        model="demo-model",
        stopReason="endTurn",
    )


async def progress_handler(progress: float, total: float | None, message: str | None):
    pct = int((progress / total) * 100) if total else 0
    print(f"Progress: {pct}% ({int(progress)}/{int(total or 0)})")


async def main():
    transport = StreamableHttpTransport(url=MCP_URL)

    async with Client(
        transport,
        elicitation_handler=elicitation_handler,
        sampling_handler=sampling_handler,
        progress_handler=progress_handler,
    ) as client:
        result = await client.call_tool("schedule_team_meeting", {"organizer": "Alex"})
        print("\nFinal result:\n")
        print(result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
