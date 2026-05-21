import sys
import asyncio
import httpx
sys.path.insert(0, "backend")

from services.calendar_service import get_upcoming_meetings
from services.agent_service import run_meeting_prep_agent

# Fetch credentials from running backend
response = httpx.get("http://localhost:8000/auth/credentials")
CREDS = response.json()

# Add this debug line
print("CREDS received:", CREDS)
print("Type:", type(CREDS))

if "error" in CREDS:
    print("Not authenticated — visit http://localhost:8000/auth/login first")
    sys.exit(1)

# Get meetings
meetings = get_upcoming_meetings(CREDS, hours_ahead=72)

if not meetings:
    print("No meetings found — add a test event to your Google Calendar with at least one attendee")
    sys.exit(1)

# Pick the first meeting and run the agent
meeting = meetings[0]
print(f"Generating brief for: {meeting['title']}")
print(f"Attendees: {meeting['attendees']}\n")

brief = asyncio.run(run_meeting_prep_agent(meeting["id"], meeting, CREDS))

print("\n" + "=" * 50)
print("MEETING BRIEF")
print("=" * 50)
print(brief)