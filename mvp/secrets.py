# mvp/secrets.py
import os
import streamlit as st

def get_secret(name: str, default: str | None = None) -> str:
    """
    Unified secrets accessor:
    - In Streamlit Cloud: reads st.secrets[name]
    - Locally: falls back to environment variables (.env or OS)
    Raises RuntimeError if the secret is missing and no default is provided.
    """
    # Streamlit Cloud / st.secrets (safe store)
    if hasattr(st, "secrets") and name in st.secrets:
        return st.secrets[name]

    # Local dev (.env or OS env)
    val = os.getenv(name, default)
    if val is None:
        raise RuntimeError(f"Missing required secret: {name}")
    return val

# in app/app.py (or mvp/secrets_helpers.py if you split it)
import requests, streamlit as st
from datetime import datetime

def save_lead(email: str, source: str = "walletglass_trial") -> None:
    """POST the lead to Formspree (or any webhook URL in secrets)."""
    url = st.secrets.get("LEADS_WEBHOOK_URL")
    if not url:
        return
    data = {
        "email": email,
        "source": source,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ua": st.session_state.get("user_agent", ""),  # optional
    }
    try:
        # Formspree accepts JSON or form-encoded; JSON is fine:
        requests.post(url, json=data, timeout=6)
    except Exception:
        pass  # never crash the app on logging
