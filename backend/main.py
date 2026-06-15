from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import RefreshError
from dotenv import load_dotenv
from services.token_store import (
    encode_value,
    decode_value,
    COOKIE_NAME,
    PKCE_COOKIE_NAME,
)
from services.calendar_service import get_upcoming_meetings
from services.agent_service import run_meeting_prep_agent
import os
import secrets
import hashlib
import base64
import traceback

# Google returns the granted scopes in a different order (and sometimes adds
# extras) than we requested, especially once "openid" is involved. Without this,
# requests-oauthlib raises "Scope has changed" during fetch_token and the
# callback 500s. Must be set before the OAuth flow runs.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

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

# Frontend (Vercel) and backend (Render) are different sites, so the auth
# cookies are cross-site: they must be SameSite=None and Secure to be sent.
_COOKIE_KW = dict(httponly=True, secure=True, samesite="none")


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


def _load_creds(request: Request):
    return decode_value(request.cookies.get(COOKIE_NAME))


def _reauth_response(message: str = "Session expired, please sign in again."):
    """Tell the frontend to restart the OAuth flow and drop the stale cookie."""
    resp = JSONResponse({"error": message, "reauth_required": True}, status_code=401)
    resp.delete_cookie(COOKIE_NAME, secure=True, samesite="none")
    return resp


@app.get("/auth/credentials")
def get_credentials(request: Request):
    creds = _load_creds(request)
    if not creds:
        return JSONResponse({"authenticated": False}, status_code=401)
    # Never echo the client secret / tokens back to the browser.
    return {"authenticated": True}

@app.get("/auth/login")
def login():
    flow = make_flow()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    resp = JSONResponse({"auth_url": auth_url})
    # Carry the PKCE verifier in a short-lived signed cookie so the callback can
    # read it even if a different worker/instance handles it (the old in-memory
    # store broke whenever Render restarted between login and callback).
    resp.set_cookie(PKCE_COOKIE_NAME, encode_value(code_verifier), max_age=600, **_COOKIE_KW)
    return resp

@app.get("/auth/callback")
def callback(request: Request, code: str, state: str = None):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    try:
        flow = make_flow()
        code_verifier = decode_value(request.cookies.get(PKCE_COOKIE_NAME))
        flow.fetch_token(code=code, code_verifier=code_verifier)
        creds = flow.credentials
    except Exception:
        # Surface the real traceback in the Render logs, then send the user back
        # to the start instead of showing a blank 500.
        traceback.print_exc()
        return RedirectResponse(f"{frontend_url}/?error=auth_failed")

    creds_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    resp = RedirectResponse(f"{frontend_url}/meetings")
    resp.set_cookie(COOKIE_NAME, encode_value(creds_dict), max_age=60 * 60 * 24 * 30, **_COOKIE_KW)
    resp.delete_cookie(PKCE_COOKIE_NAME, secure=True, samesite="none")
    return resp

@app.get("/auth/token")
def get_token(request: Request):
    creds = _load_creds(request)
    if not creds:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    return {"token": creds["token"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/meetings")
def list_meetings(request: Request):
    creds = _load_creds(request)
    if not creds:
        return _reauth_response("Not authenticated")
    try:
        meetings = get_upcoming_meetings(creds, hours_ahead=72)
    except RefreshError:
        # The stored Google token can no longer be refreshed (revoked, or a
        # Testing-mode refresh token that expired after 7 days). Re-auth.
        traceback.print_exc()
        return _reauth_response()
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": "Failed to load meetings", "detail": str(e)}, status_code=500)
    return {"meetings": meetings}

@app.post("/meetings/{event_id}/brief")
async def generate_brief(event_id: str, request: Request):
    creds = _load_creds(request)
    if not creds:
        return _reauth_response("Not authenticated")
    try:
        meetings = get_upcoming_meetings(creds, hours_ahead=72)
        event = next((m for m in meetings if m["id"] == event_id), None)
        if not event:
            return JSONResponse({"error": "Event not found"}, status_code=404)
        brief = await run_meeting_prep_agent(event_id, event, creds)
    except RefreshError:
        traceback.print_exc()
        return _reauth_response()
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"error": "Failed to generate brief", "detail": str(e)}, status_code=500)
    return {"brief": brief}
