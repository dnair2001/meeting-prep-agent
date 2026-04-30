import json
import os

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "token.json")

def save_credentials(creds: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(creds, f)

def load_credentials() -> dict | None:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def clear_credentials():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)