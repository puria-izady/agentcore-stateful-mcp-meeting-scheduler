from __future__ import annotations

import asyncio
import os

import boto3
import httpx
from botocore.auth import SigV4Auth as BotoSigV4Auth
from botocore.awsrequest import AWSRequest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp.types import CreateMessageResult, TextContent

RUNTIME_URL = os.environ["AGENTCORE_RUNTIME_URL"]
AWS_PROFILE = os.environ.get("AWS_PROFILE", "default")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

RESPONSES = iter(
    [
        {"topic": "Weekly Product Sync"},
        {"participants": "Alex, Sam, Jordan"},
        {"meeting_date": "2026-04-22"},
        {"duration_minutes": 45},
        {"confirm": "yes"},
    ]
)


class SigV4Auth(httpx.Auth):
    requires_request_body = True

    def __init__(self, profile: str, region: str, service: str = "bedrock-agentcore"):
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.region = region
        self.service = service

    def auth_flow(self, request):
        credentials = self.session.get_credentials().get_frozen_credentials()
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=dict(request.headers),
        )
        BotoSigV4Auth(credentials, self.service, self.region).add_auth(aws_request)
        request.headers.clear()
        for key, value in aws_request.headers.items():
            request.headers[key] = value
        yield request


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
    transport = StreamableHttpTransport(
        url=RUNTIME_URL,
        auth=SigV4Auth(AWS_PROFILE, AWS_REGION),
    )

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
