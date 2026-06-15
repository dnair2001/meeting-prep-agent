import json
import os
import hmac
import hashlib
import base64

# Names of the signed cookies we set on the client. Credentials no longer live
# on disk (Render's filesystem is ephemeral and wiped on every redeploy/spin-down)
# nor in process memory (lost across restarts and not shared between workers).
COOKIE_NAME = "mpa_creds"
PKCE_COOKIE_NAME = "mpa_pkce"

# Must be a stable value across instances/redeploys, otherwise existing cookies
# stop validating. Set SECRET_KEY in the environment (Render dashboard).
_SECRET = os.getenv("SECRET_KEY", "insecure-dev-secret-set-SECRET_KEY").encode()


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(payload: bytes) -> str:
    sig = hmac.new(_SECRET, payload, hashlib.sha256).digest()
    return f"{_b64encode(payload)}.{_b64encode(sig)}"


def _unsign(token: str) -> bytes | None:
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload = _b64decode(payload_b64)
        expected = hmac.new(_SECRET, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(_b64decode(sig_b64), expected):
            return None
        return payload
    except Exception:
        return None


def encode_value(value) -> str:
    """Serialize and HMAC-sign a JSON-able value for storage in a cookie."""
    return _sign(json.dumps(value).encode())


def decode_value(token: str | None):
    """Verify and decode a signed cookie value; returns None if missing/tampered."""
    if not token:
        return None
    payload = _unsign(token)
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return None
