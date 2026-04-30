from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
from services.token_store import save_credentials, load_credentials
from services.calendar_service import get_upcoming_meetings
from services.agent_service import run_meeting_prep_agent
import os
import secrets
import hashlib
import base64

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "http://localhost:3000",
        "https://meeting-prep-agent-amber.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]

# In-memory store only for the code verifier (used during OAuth flow)
_state_store = {}

def generate_code_verifier():
    return secrets.token_urlsafe(32)

def generate_code_challenge(verifier: str):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

def make_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    )

@app.get("/auth/credentials")
def get_credentials():
    creds = load_credentials()
    if not creds:
        return {"error": "Not authenticated"}
    return creds

@app.get("/auth/login")
def login():
    flow = make_flow()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    _state_store["code_verifier"] = code_verifier
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    return {"auth_url": auth_url}

@app.get("/auth/callback")
def callback(request: Request, code: str, state: str = None):
    flow = make_flow()
    code_verifier = _state_store.get("code_verifier")
    flow.fetch_token(code=code, code_verifier=code_verifier)
    creds = flow.credentials
    save_credentials({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "token_uri": "https://oauth2.googleapis.com/token",
    })
    return RedirectResponse("http://localhost:3000/meetings")
    
@app.get("/auth/token")
def get_token():
    creds = load_credentials()
    if not creds:
        return {"error": "Not authenticated"}
    return {"token": creds["token"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/meetings")
def list_meetings():
    creds = load_credentials()
    if not creds:
        return {"error": "Not authenticated"}
    meetings = get_upcoming_meetings(creds, hours_ahead=72)
    return {"meetings": meetings}

@app.post("/meetings/{event_id}/brief")
def generate_brief(event_id: str):
    creds = load_credentials()
    if not creds:
        return {"error": "Not authenticated"}
    meetings = get_upcoming_meetings(creds, hours_ahead=72)
    event = next((m for m in meetings if m["id"] == event_id), None)
    if not event:
        return {"error": "Event not found"}
    brief = run_meeting_prep_agent(event_id, event, creds)
    return {"brief": brief}