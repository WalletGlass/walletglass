# app/app.py
# WalletGlass MVP v2 — Streamlit UI
# Purpose: Single-page app that shows ROI = (Current - Funded) / Funded for a wallet.
# Behavior: Address input (auto-run), validation, cached fetches, results cards, Pro-gated token tile, last-address persistence.

import json
import re
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
from dotenv import load_dotenv
# Load minimal CSS (kept safe and small)
from pathlib import Path

css_path = Path(__file__).with_name("theme.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# --- Config & Theme ---
st.set_page_config(
    page_title="WalletGlass — ROI, not vibes.",
    page_icon="💎",
    layout="centered",
    initial_sidebar_state="collapsed"
)
# (Dark mode is a user preference in Streamlit; we’ll design for dark. Optionally add a theme in .streamlit/config.toml)

# --- Load env keys (if your SDKs read from env) ---
load_dotenv()

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
LAST_ADDR_FILE = DATA_DIR / "last_address.json"

DEMO_ADDR = "0xc0ffee254729296a45a3885639AC7E10F9d54979"
ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Free-tier throttle (one new address per 5 minutes)
THROTTLE_MINUTES = 5

# TODO: replace these with real functions from your modules
def get_funding(address: str) -> dict:
    # from mvp.funding import get_funding
    # return get_funding(address)
    return {"funded_usd": 1234.56, "events": []}  # placeholder

def get_portfolio(address: str) -> dict:
    # from mvp.balances import get_portfolio
    # return get_portfolio(address)
    return {"current_value_usd": 1412.34, "tokens": []}  # placeholder

def compute_pnl(funded_usd: float, current_value_usd: float) -> dict:
    # from mvp.pnl import compute_pnl
    # return compute_pnl(funded_usd, current_value_usd)
    net = current_value_usd - funded_usd
    roi = (net / funded_usd * 100.0) if funded_usd > 0 else 0.0
    return {
        "funded_usd": round(funded_usd, 2),
        "current_value_usd": round(current_value_usd, 2),
        "net_pnl_usd": round(net, 2),
        "roi_pct": round(roi, 2),
    }

@st.cache_data(ttl=600, show_spinner=False)
def cached_funding(address: str) -> dict:
    return get_funding(address)

@st.cache_data(ttl=600, show_spinner=False)
def cached_portfolio(address: str) -> dict:
    return get_portfolio(address)

def save_last_address(addr: str):
    try:
        LAST_ADDR_FILE.write_text(json.dumps({"address": addr, "ts": datetime.utcnow().isoformat()}))
    except Exception:
        pass

def load_last_address() -> str | None:
    try:
        obj = json.loads(LAST_ADDR_FILE.read_text())
        return obj.get("address")
    except Exception:
        return None

def format_usd(x: float) -> str:
    return f"${x:,.2f}"

# --- Header ---
left, right = st.columns([1, 4])
with left:
    logo_path = Path(__file__).with_name("assets") / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)
with right:
    st.markdown("### 💎 WalletGlass")
    st.caption("**Because vibes aren’t a trading strategy.**")

# --- Session / throttle setup ---
if "last_switch_ts" not in st.session_state:
    st.session_state.last_switch_ts = None
if "active_address" not in st.session_state:
    st.session_state.active_address = load_last_address() or DEMO_ADDR

# --- Address input ---
col1, col2 = st.columns([3, 1])
with col1:
    addr = st.text_input(
        "Wallet address (EVM)",
        value=st.session_state.active_address,
        placeholder="0x…",
        help="Enter a valid EVM address. Press Enter to analyze."
    )
with col2:
    if st.button("Use last"):
        last = load_last_address()
        if last:
            addr = last
            st.success("Loaded last address.")

# Validate
if not ADDR_RE.match(addr):
    st.warning("Please enter a valid EVM address (0x + 40 hex chars).")
    st.stop()

# Free-tier throttle (only if switching to a *new* address)
is_new_address = addr.lower() != (st.session_state.active_address or "").lower()
if is_new_address:
    now = datetime.utcnow()
    if st.session_state.last_switch_ts and now - st.session_state.last_switch_ts < timedelta(minutes=THROTTLE_MINUTES):
        retry_at = st.session_state.last_switch_ts + timedelta(minutes=THROTTLE_MINUTES)
        st.info(f"Free-tier rate limit: try another address after {retry_at.strftime('%H:%M UTC')}.")
        st.stop()
    # allow switch
    st.session_state.last_switch_ts = now
    st.session_state.active_address = addr
    save_last_address(addr)

# --- Pipeline status ---
with st.status("Running analysis…", expanded=False) as status:
    status.update(label="1/3 Fetching funding…")
    try:
        funding = cached_funding(addr)
        funded_usd = float(funding.get("funded_usd", 0.0))
    except Exception as e:
        st.error(f"Funding error: {e}")
        status.update(state="error")
        st.stop()

    status.update(label="2/3 Fetching balances…")
    try:
        portfolio = cached_portfolio(addr)
        current_usd = float(portfolio.get("current_value_usd", 0.0))
    except Exception as e:
        st.error(f"Balances error: {e}")
        status.update(state="error")
        st.stop()

    status.update(label="3/3 Computing ROI…")
    pnl = compute_pnl(funded_usd, current_usd)
    status.update(label="Done", state="complete")

# --- Results ---
st.subheader("Your ROI snapshot")

c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

c1.metric("Total Funded", format_usd(pnl["funded_usd"]))
c2.metric("Current Value", format_usd(pnl["current_value_usd"]))
delta = f'{format_usd(pnl["net_pnl_usd"])}'
c3.metric("Net PnL", delta)
c4.metric("ROI", f'{pnl["roi_pct"]}%')

# Pro-gated token view
st.divider()
pro_col = st.container()
pro_col.markdown("#### 🔒 Top 5 tokens (Pro)")
pro_col.caption("Upgrade to see token-level breakdown and trends.")
pro_col.button("Upgrade", disabled=True)

# Downloads
st.divider()
dl1, dl2, dl3 = st.columns(3)
with dl1:
    st.download_button("Download funding.json", data=json.dumps(funding, indent=2), file_name="wallet_funding.json")
with dl2:
    st.download_button("Download portfolio.json", data=json.dumps(portfolio, indent=2), file_name="wallet_portfolio.json")
with dl3:
    st.download_button("Download pnl.json", data=json.dumps(pnl, indent=2), file_name="wallet_pnl.json")

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
