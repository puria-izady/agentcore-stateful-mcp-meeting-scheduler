from __future__ import annotations

import asyncio
from typing import Literal

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("meeting-scheduler-stateful")

ROOMS = [
    {"name": "Atlas", "capacity": 4},
    {"name": "Zephyr", "capacity": 8},
    {"name": "Orion", "capacity": 12},
]

TIME_SLOTS = ["09:30", "11:00", "14:00", "16:00"]


class TopicInput(BaseModel):
    topic: str = Field(description="Meeting topic, for example Sprint Planning")


class ParticipantsInput(BaseModel):
    participants: str = Field(
        description="Comma-separated list of attendees, for example Alex, Sam, Jordan"
    )


class DateInput(BaseModel):
    meeting_date: str = Field(description="Meeting date, for example 2026-04-22")


class DurationInput(BaseModel):
    duration_minutes: int = Field(ge=15, le=180)


class ConfirmInput(BaseModel):
    confirm: Literal["yes", "no"]


@mcp.resource("meeting://rooms")
def meeting_rooms() -> str:
    lines = ["Available meeting rooms:"]
    for room in ROOMS:
        lines.append(f"- {room['name']} (capacity: {room['capacity']})")
    return "\n".join(lines)


@mcp.prompt()
def invite_prompt(topic: str, date: str, time: str, duration: int, participants: str) -> str:
    return (
        f"Write a concise internal meeting invite for '{topic}' on {date} at {time} "
        f"for {duration} minutes with attendees {participants}. Include a short agenda."
    )


@mcp.tool()
async def schedule_team_meeting(organizer: str, ctx: Context) -> str:
    """Schedule a team meeting through a stateful MCP interaction."""

    topic_result = await ctx.elicit("What is the meeting about?", TopicInput)
    if not hasattr(topic_result, "data"):
        return "Meeting scheduling cancelled before collecting the topic."
    topic = topic_result.data.topic

    participants_result = await ctx.elicit(
        "Who should attend? Provide a comma-separated list.",
        ParticipantsInput,
    )
    if not hasattr(participants_result, "data"):
        return "Meeting scheduling cancelled before collecting participants."
    participants = [
        name.strip()
        for name in participants_result.data.participants.split(",")
        if name.strip()
    ]
    participant_count = max(len(participants), 1)

    date_result = await ctx.elicit("What date should I optimize for?", DateInput)
    if not hasattr(date_result, "data"):
        return "Meeting scheduling cancelled before collecting the date."
    meeting_date = date_result.data.meeting_date

    duration_result = await ctx.elicit(
        "How long should the meeting be in minutes?",
        DurationInput,
    )
    if not hasattr(duration_result, "data"):
        return "Meeting scheduling cancelled before collecting the duration."
    duration_minutes = duration_result.data.duration_minutes

    confirm_result = await ctx.elicit(
        (
            f"Confirm scheduling '{topic}' for {', '.join(participants)} on {meeting_date} "
            f"for {duration_minutes} minutes. Reply yes or no."
        ),
        ConfirmInput,
    )
    if not hasattr(confirm_result, "data") or confirm_result.data.confirm != "yes":
        return "Meeting scheduling cancelled at confirmation step."

    total_steps = 4

    await ctx.report_progress(progress=1, total=total_steps)
    await asyncio.sleep(0.4)
    chosen_time = TIME_SLOTS[(participant_count + duration_minutes // 30) % len(TIME_SLOTS)]

    await ctx.report_progress(progress=2, total=total_steps)
    candidate_rooms = [room for room in ROOMS if room["capacity"] >= participant_count]
    chosen_room = candidate_rooms[0] if candidate_rooms else ROOMS[-1]
    await asyncio.sleep(0.4)

    await ctx.report_progress(progress=3, total=total_steps)
    sampling_prompt = f"""
You are helping draft an internal team meeting invite.

Create a concise invite message for this meeting:
- Organizer: {organizer}
- Topic: {topic}
- Date: {meeting_date}
- Time: {chosen_time}
- Duration: {duration_minutes} minutes
- Participants: {', '.join(participants)}
- Room: {chosen_room['name']}

Requirements:
- Keep it under 140 words
- Include a short reason for the meeting
- Include a 3-bullet agenda
- Sound clear and professional
""".strip()

    invite_text = "Invite draft unavailable."
    try:
        sample_result = await ctx.sample(messages=sampling_prompt, max_tokens=300)
        if hasattr(sample_result, "text") and sample_result.text:
            invite_text = sample_result.text
    except Exception as exc:
        invite_text = f"Sampling failed: {exc}"

    await ctx.report_progress(progress=4, total=total_steps)

    return (
        f"Meeting scheduled successfully\n"
        f"Organizer: {organizer}\n"
        f"Topic: {topic}\n"
        f"Date: {meeting_date}\n"
        f"Time: {chosen_time}\n"
        f"Duration: {duration_minutes} minutes\n"
        f"Room: {chosen_room['name']}\n"
        f"Attendees: {', '.join(participants)}\n\n"
        f"Invite draft:\n{invite_text}"
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        stateless_http=False,
    )
