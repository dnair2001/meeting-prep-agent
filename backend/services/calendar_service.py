from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timezone, timedelta

def get_upcoming_meetings(creds_dict: dict, hours_ahead: int = 24):
    creds = Credentials(
        token=creds_dict["token"],
        refresh_token=creds_dict["refresh_token"],
        client_id=creds_dict["client_id"],
        client_secret=creds_dict["client_secret"],
        token_uri=creds_dict["token_uri"],
    )
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=hours_ahead)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for e in result.get("items", []):
        attendees = [
            a["email"] for a in e.get("attendees", [])
            if not a.get("self", False)
        ]
        events.append({
            "id": e["id"],
            "title": e.get("summary", "Untitled"),
            "start": e["start"].get("dateTime"),
            "attendees": attendees,
            "agenda": e.get("description", ""),
        })

    return events