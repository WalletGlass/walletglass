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
