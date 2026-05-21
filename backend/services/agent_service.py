import anthropic
import asyncio
import json
from .calendar_service import get_upcoming_meetings
from .gmail_service import get_recent_threads

client = anthropic.AsyncAnthropic()

TOOLS = [
    {
        "name": "get_calendar_event",
        "description": "Get full details of the meeting including attendees and agenda.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The Google Calendar event ID"
                }
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "get_gmail_threads",
        "description": "Fetch recent email threads with the meeting attendees from Gmail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "attendee_emails": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses"
                }
            },
            "required": ["attendee_emails"],
        },
    },
    {
        "name": "search_web",
        "description": "Search the web to research a meeting attendee or their company.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query e.g. 'Alice Smith engineer at Stripe'"
                }
            },
            "required": ["query"],
        },
    },
]

async def execute_tool(tool_name: str, tool_input: dict, creds_dict: dict, event_data: dict):
    print(f"  -> Executing tool: {tool_name} with input: {tool_input}")

    if tool_name == "get_calendar_event":
        return event_data

    elif tool_name == "get_gmail_threads":
        # googleapiclient is sync — offload to a thread so it doesn't block the event loop
        return await asyncio.to_thread(
            get_recent_threads, creds_dict, tool_input["attendee_emails"]
        )

    elif tool_name == "search_web":
        # Sub-call to Claude with web search enabled (async — runs concurrently with sibling tool calls)
        result = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": tool_input["query"]}],
        )
        for block in result.content:
            if hasattr(block, "text"):
                return block.text
        return "No results found"

    return "Unknown tool"

async def run_meeting_prep_agent(event_id: str, event_data: dict, creds_dict: dict) -> str:
    system_prompt = """You are a meeting preparation assistant. Given a calendar event,
you research the attendees and context, then produce a concise meeting brief.

Your brief must include these sections:
1. **Meeting Overview** — title, time, who's attending
2. **Attendee Profiles** — role, company, what they work on (use web search)
3. **Recent Email Context** — what have you discussed with them lately
4. **Suggested Talking Points** — based on the agenda and context
5. **Open Items** — any follow-ups or unresolved threads to address

Be specific and actionable. Keep the total brief under 400 words."""

    messages = [
        {
            "role": "user",
            "content": f"""Prepare a meeting brief for this event:

Title: {event_data['title']}
Time: {event_data['start']}
Attendees: {', '.join(event_data['attendees']) if event_data['attendees'] else 'No external attendees'}
Agenda: {event_data.get('agenda') or 'No agenda provided'}
Event ID: {event_id}

Use your tools to research the attendees and pull recent email context, then write the brief."""
        }
    ]

    print(f"\nStarting agent for: {event_data['title']}")

    # Agent loop
    while True:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        print(f"  Stop reason: {response.stop_reason}")

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        # Claude is done — extract and return the text
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "No brief generated"

        # Claude wants to use tools — fan out all tool calls in parallel
        if response.stop_reason == "tool_use":
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            results = await asyncio.gather(*[
                execute_tool(b.name, b.input, creds_dict, event_data)
                for b in tool_use_blocks
            ])

            tool_results = [
                {
                    "type": "tool_result",
                    "tool_use_id": b.id,
                    "content": json.dumps(r),
                }
                for b, r in zip(tool_use_blocks, results)
            ]

            # Send all results back in one user turn
            messages.append({"role": "user", "content": tool_results})