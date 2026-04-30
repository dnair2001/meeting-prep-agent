from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64

def get_recent_threads(creds_dict: dict, attendee_emails: list, max_results: int = 5):
    creds = Credentials(
        token=creds_dict["token"],
        refresh_token=creds_dict["refresh_token"],
        client_id=creds_dict["client_id"],
        client_secret=creds_dict["client_secret"],
        token_uri=creds_dict["token_uri"],
    )
    service = build("gmail", "v1", credentials=creds)

    query = " OR ".join([f"from:{e}" for e in attendee_emails])
    query += " newer_than:30d"

    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    threads = []
    for msg in result.get("messages", []):
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="full",
        ).execute()

        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
        body = _extract_body(detail["payload"])

        threads.append({
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": detail.get("snippet", ""),
            "body": body[:500],
        })

    return threads

def _extract_body(payload):
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(
            payload["body"]["data"]
        ).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return ""