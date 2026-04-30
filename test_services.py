# test_services.py
import sys
sys.path.insert(0, "backend")

from services.calendar_service import get_upcoming_meetings
from services.gmail_service import get_recent_threads

# Paste your token from http://localhost:8000/auth/token here
TOKEN = "ya29.a0AQvPyIMF5Ljkoe-7ayXrz9nepOGDVPxORdnyst02jMye5C5-mZHdO9nJqkZUMN26nmfu6qlTnbP5enlPFSzhoUj0ZysAnDLjVWhUUqTQ4CESdo_Hh_DdC2usIBecx2aRKbaxROqBT6uJFC292Ss82FKgArLlVTlIwQ1rOenqwYfcXcd39ubXHyKl-iZUeIGE9ThUYVEaCgYKARUSARESFQHGX2MiOpXQNYu4q7wGK2MJhAcDVw0206"

print("=== CALENDAR ===")
meetings = get_upcoming_meetings(TOKEN, hours_ahead=72)

if not meetings:
    print("No meetings found in next 72 hours — try adding a test event to your Google Calendar")
else:
    for m in meetings:
        print(f"\nTitle: {m['title']}")
        print(f"Start: {m['start']}")
        print(f"Attendees: {m['attendees']}")
        print(f"Agenda: {m['agenda'][:100] if m['agenda'] else '(none)'}")

print("\n=== GMAIL ===")
if meetings and meetings[0]["attendees"]:
    test_emails = meetings[0]["attendees"]
    print(f"Searching threads with: {test_emails}")
    threads = get_recent_threads(TOKEN, test_emails)

    if not threads:
        print("No recent threads found with those attendees")
    else:
        for t in threads:
            print(f"\nSubject: {t['subject']}")
            print(f"From: {t['from']}")
            print(f"Snippet: {t['snippet'][:150]}")
else:
    print("No attendees found to test Gmail with — add someone to a calendar event")