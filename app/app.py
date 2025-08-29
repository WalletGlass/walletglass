# app/app.py
# WalletGlass MVP v2 — Streamlit UI
# Purpose: Single-page app that shows ROI = (Current - Funded) / Funded for a wallet.
# Behavior: Address input (auto-run), validation, cached fetches, results cards, Pro-gated token tile, last-address persistence.

import os, sys, pathlib, json, re
from pathlib import Path
from datetime import datetime, timedelta

# Make sure project root is importable
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import streamlit as st
from dotenv import load_dotenv

# Real module imports (keep these!)
from mvp.funding_v1 import get_funding
from mvp.balances_moralis import get_portfolio
from mvp.pnl import compute_pnl
from mvp.defunding import get_defunding
from mvp.secrets import get_secret, save_lead

# --- Email-based rate limit (persisted to disk) ---
import hashlib

RATE_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "rate_limit.json"
THROTTLE_MINUTES = 60  # (jargon: configurable constant) (plain: 1 hour per email for new addresses)

def _email_key(email: str) -> str:
    """Stable, privacy-friendly key for disk (hash of email).
    (jargon: salted/hashed identifier) (plain: we don't store the raw email on disk)"""
    e = (email or "").strip().lower()
    return hashlib.sha256(e.encode("utf-8")).hexdigest()[:16]

def _load_rate_db() -> dict:
    try:
        RATE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        if RATE_DB_PATH.exists():
            return json.loads(RATE_DB_PATH.read_text())
        return {}
    except Exception:
        return {}

def _save_rate_db(db: dict) -> None:
    try:
        tmp = RATE_DB_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(db, indent=2))
        tmp.replace(RATE_DB_PATH)
    except Exception:
        pass

def enforce_rate_limit(email: str, address: str) -> tuple[bool, str | None]:
    """
    Return (ok, retry_at_str). If ok=False, caller should stop and show retry time.
    (jargon: gatekeeper) (plain: decides if this email can analyze a new address now)
    """
    if not email:
        # if somehow we got here without the gate, be safe and allow
        return True, None

    db = _load_rate_db()
    key = _email_key(email)
    rec = db.get(key, {"last_addr": None, "last_ts": None})

    # Is this a NEW address? (we only throttle new addresses; re-running same addr is fine)
    is_new = (address or "").lower() != (rec.get("last_addr") or "").lower()

    if not is_new:
        return True, None  # same address → always ok

    # If we’ve never seen this email, allow and record
    now = datetime.utcnow()
    if not rec.get("last_ts"):
        rec = {"last_addr": address, "last_ts": now.isoformat()}
        db[key] = rec
        _save_rate_db(db)
        return True, None

    # If seen: check elapsed time
    try:
        last_ts = datetime.fromisoformat(rec["last_ts"])
    except Exception:
        last_ts = now

    delta = now - last_ts
    if delta < timedelta(minutes=THROTTLE_MINUTES):
        retry_at = (last_ts + timedelta(minutes=THROTTLE_MINUTES)).strftime("%H:%M UTC")
        return False, retry_at

    # Passed window → allow and update
    rec = {"last_addr": address, "last_ts": now.isoformat()}
    db[key] = rec
    _save_rate_db(db)
    return True, None

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.I)
DISPOSABLE = {"mailinator.com", "10minutemail.com", "tempmail.com", "sharklasers.com"}  # tiny optional list

def _is_disposable(email: str) -> bool:
    try:
        return email.split("@", 1)[1].lower() in DISPOSABLE
    except Exception:
        return True

def email_gate() -> bool:
    """
    Show a small form and return True once the user passes the gate.
    [jargon: session flag → a value stored for this browser tab]
    """
    if st.session_state.get("email_ok"):
        return True

    st.markdown("### ✉️ Try WalletGlass free")
    st.write("Enter your email to unlock the demo. We’ll send occasional updates (no spam).")

    with st.form("email_gate", clear_on_submit=False):
        email = st.text_input("Email address", placeholder="you@example.com")
        consent = st.checkbox("I agree to the Terms & Privacy", value=True)
        submit = st.form_submit_button("Continue")

    if submit:
        email = (email or "").strip()
        if not EMAIL_RE.match(email):
            st.error("Please enter a valid email address.")
            return False
        if _is_disposable(email):
            st.error("Please use a non-disposable email.")
            return False
        if not consent:
            st.error("Please accept the terms to continue.")
            return False

        # passed ✅
        st.session_state.email_ok = True
        st.session_state.user_email = email
        save_lead(email)  # will no-op if LEADS_WEBHOOK_URL is not set
        st.success("You're in!")
        return True

    return False

# Page config FIRST

# --- Config & Theme (must be first) ---
favicon_path = Path(__file__).resolve().parent / "assets" / "favicon.ico"
st.set_page_config(
    page_title="WalletGlass — ROI, not vibes.",
    page_icon=str(favicon_path) if favicon_path.exists() else "💎",
    layout="centered",
    initial_sidebar_state="collapsed",
)
# --- Email gate must run before the pipeline/UI ---
if not email_gate():
    st.stop()

with st.sidebar:
    if st.session_state.get("user_email"):
        st.caption(f"Signed in as **{st.session_state['user_email']}**")


def _require_secrets():
    try:
        # Touch the keys to force a clear error early
        _ = get_secret("MORALIS_API_KEY")
        _ = get_secret("ETHERSCAN_API_KEY")
    except RuntimeError as e:
        import streamlit as st
        st.error(str(e))
        st.stop()

_require_secrets()


st.markdown("""
<style>
/* Hide footer / “Made with Streamlit” badge */
footer {visibility: hidden;}
/* Hide the top toolbar (deploy/fork badge area on Community Cloud) */
[data-testid="stToolbar"] {display: none;}
/* Hide the hamburger MainMenu (we already removed items via menu_items) */
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Reduce the top padding in the main app */
.block-container {
    padding-top: 1rem;   /* default is ~6rem; try 0 or 1rem */
}
</style>
""", unsafe_allow_html=True)

from urllib.parse import urlencode

def use_dev_mode() -> bool:
    """Enable Developer Mode only if the logged-in email is allowed."""
    # Add your email(s) here
    allowed = {"tylerwares1@gmail.com","twares@hotmail.ca"}  

    user_email = st.session_state.get("user_email")
    if user_email not in allowed:
        return False  # hide Dev Mode entirely for others

    qp = st.query_params
    default = qp.get("dev", ["0"])[0] in ("1", "true", "True")
    dev = st.sidebar.toggle("🛠️ Developer Mode", value=default, help="Show debug info & sanity panels")
    if dev and not default:
        st.query_params.update({"dev": "1"})
    if (not dev) and default:
        st.query_params.update({"dev": "0"})
    return dev


DEV = use_dev_mode()

if DEV:
    st.caption("🛠️ Developer Mode is enabled.")
    # Debug info (optional)
    st.caption(f"CWD: {os.getcwd()}")
    st.caption("Top sys.path entries:")
    for p in sys.path[:5]:
        st.caption(f"• {p}")
    st.caption(f"mvp exists: {pathlib.Path(__file__).resolve().parents[1].joinpath('mvp').exists()}")
if DEV and st.sidebar.button("Reset my rate limit"):
    db = _load_rate_db()
    key = _email_key(st.session_state.get("user_email",""))
    if key in db:
        db.pop(key, None)
        _save_rate_db(db)
        st.success("Rate limit reset for your email.")

# ... (CSS load, helpers, etc.)

@st.cache_data(ttl=600, show_spinner=False)
def cached_funding(address: str) -> dict:
    return get_funding(address)      # uses imported function

@st.cache_data(ttl=600, show_spinner=False)
def cached_portfolio(address: str) -> dict:
    return get_portfolio(address)    # uses imported function

@st.cache_data(ttl=600, show_spinner=False)
def cached_defunding(address: str) -> dict:
    return get_defunding(address)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
LAST_ADDR_FILE = DATA_DIR / "last_address.json"

DEMO_ADDR = "0xc0ffee254729296a45a3885639AC7E10F9d54979"
ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

# Free-tier throttle (one new address per 5 minutes)
THROTTLE_MINUTES = 60

css_path = Path(__file__).with_name("theme.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
def _fmt_err(e: Exception) -> str:
    # (pretty error string)
    return f"{type(e).__name__}: {getattr(e, 'args', [''])[0]}"
if DEV:
    with st.expander("🧪 Funding sanity panel", expanded=False):
        st.caption("Quick visibility into imports, caching, and return shape.")

        # Show exactly what we’re importing
        try:
            import inspect, mvp.funding_v1 as funding_mod
            st.write("**funding_v1 path:**", inspect.getsourcefile(funding_mod))
            st.write("**has `get_funding`?**", hasattr(funding_mod, "get_funding"))
        except Exception as e:
            st.error("Import problem: " + _fmt_err(e))

        # Dry-run call (no cache) against the current address, but don't block the main pipeline
        try:
            test_addr = st.session_state.get("active_address", None) or DEMO_ADDR
            if st.button("Run quick get_funding() test"):
                out = get_funding(test_addr)  # direct call (bypasses cache)
                st.success(f"get_funding() OK — funded_usd={out.get('funded_usd')}, events={len(out.get('events', []))}")
                st.json({k: out[k] for k in ("funded_usd",) if k in out})
                # Only preview a few events so UI stays snappy
                ev = out.get("events", [])[:5]
                if ev:
                    st.write("First 5 events:")
                    st.json(ev)
                else:
                    st.info("No events returned.")
        except Exception as e:
            st.error("get_funding() raised an error: " + _fmt_err(e))
            st.exception(e)  # full traceback, helpful during dev

if DEV:
    with st.expander("🧪 Portfolio sanity panel", expanded=False):
        if st.button("Run quick get_portfolio() test"):
            out = get_portfolio(st.session_state.get("active_address", DEMO_ADDR))
            st.success(f"current_value_usd={out.get('current_value_usd')}, tokens={len(out.get('tokens', []))}")
            st.json({"current_value_usd": out.get("current_value_usd")})
            st.write("Top tokens (up to 10):")
            st.json(out.get("tokens", [])[:10])



# --- Load env keys (if your SDKs read from env) ---
load_dotenv()

@st.cache_data(ttl=600, show_spinner=False)
def cached_funding(address: str) -> dict:
    return get_funding(address)   # ← imported from mvp.funding_v1

@st.cache_data(ttl=600, show_spinner=False)
def cached_portfolio(address: str) -> dict:
    return get_portfolio(address) # ← imported from mvp.balances_moralis

@st.cache_data(ttl=600, show_spinner=False)
def cached_defunding(address: str) -> dict:
    return get_defunding(address)

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

def signed_usd(x: float) -> str:
    """Return +$1,234.56 or -$1,234.56."""
    sign = "+" if x >= 0 else "-"
    return f"{sign}${abs(x):,.2f}"

def roi_delta_color(roi_pct: float) -> str:
    """Return a Streamlit delta color: 'normal' (green up / red down) or 'off'."""
    return "normal" if abs(roi_pct) >= 0.10 else "off"  # 0.10% = near-zero threshold

# --- Header ---
left, right = st.columns([1,1])
with left:
    logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
    if logo_path.exists():
        # Streamlit serves it safely, scales with width %
        st.image(str(logo_path), use_container_width=True)
        
    else:
        st.markdown("### 💎 WalletGlass")
st.markdown(
        "<div style='margin-center:-36px; font-size:1.5rem; color:#9aa0a6;'>"
        "Because vibes aren’t a trading strategy."
        "</div>",
        unsafe_allow_html=True
    )
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
# --- Free-tier throttle (per-email; only when switching to a new address) ---
user_email = st.session_state.get("user_email", "")
ok, retry_at = enforce_rate_limit(user_email, addr)
if not ok:
    st.info(f"Free-tier rate limit (per email): try another address after {retry_at}.")
    st.stop()

# If allowed AND it is new, persist the UI's notion of "active address" as well
is_new_address = addr.lower() != (st.session_state.get("active_address") or "").lower()
if is_new_address:
    st.session_state.active_address = addr
    save_last_address(addr)  # your existing helper


# --- Pipeline status ---
with st.status("Running analysis…", expanded=False) as status:
    status.update(label="1/3 Fetching funding (Moralis + Etherscan checks)…")
    try:
        funding = cached_funding(addr)   # (jargon: cache = memoized data; speeds up repeats)
        funded_usd = float(funding.get("funded_usd", 0.0))
        funding_events = funding.get("events", [])
    except Exception as e:
        st.error("Funding error: " + _fmt_err(e))
        status.update(state="error")
        st.stop()
    # NEW: defunding (tiny extra call; also cached)
    try:
        defunding = cached_defunding(addr)
        defunded_usd = float(defunding.get("defunded_usd", 0.0))
        defund_events = defunding.get("events", [])
    except Exception as e:
        st.error("Defunding error: " + _fmt_err(e))
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
    try:
        pnl = compute_pnl(funded_usd, defunded_usd, current_usd)
    except Exception as e:
        st.error(f"PnL error: {e}")
        status.update(state="error")
        st.stop()
    status.update(label="Done", state="complete")


if DEV:
    with st.expander("🧪 PnL sanity panel", expanded=False):
        st.caption("Uses the two upstream totals to compute net & ROI.")
        st.json({
            "funded_usd": funded_usd,
            "current_value_usd": current_usd,
            "computed": pnl
        })
if DEV:
    with st.expander("🧪 Defunding sanity panel", expanded=False):
        st.caption(f"{len(defund_events)} outbound events (first 10 shown)")
        st.json(defund_events[:10])

# --- Results ---
st.subheader("Your ROI snapshot")

c1, c2, c5 = st.columns([1,1,1])
c1.metric("Total Funded", format_usd(funded_usd))
c2.metric("Current Value", format_usd(current_usd))
c5.metric("Total Defunded", format_usd(defunded_usd))

net = float(pnl["net_pnl_usd"])
roi = float(pnl["roi_pct"])
dc = roi_delta_color(roi)

c3,c4 = st.columns(2)
# Net PnL card: show the number as value, color via ROI delta
c3.metric(
    "Net PnL",
    format_usd(net),
    delta=f"{roi:+.2f}%",
    delta_color=dc
)

# ROI card: show ROI as value, color via Net PnL size/sign (nice reinforcement)
c4.metric(
    "ROI",
    f"{roi:.2f}%",
    delta=signed_usd(net),
    delta_color=dc
)


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
    st.download_button("Download funding.json",
        data=json.dumps(funding, indent=2), file_name="wallet_funding.json")
with dl2:
    st.download_button("Download portfolio.json",
        data=json.dumps(portfolio, indent=2), file_name="wallet_portfolio.json")
with dl3:
    st.download_button("Download pnl.json",
        data=json.dumps(pnl, indent=2), file_name="wallet_pnl.json")
# NEW:
with st.columns(3)[0]:
    st.download_button("Download defunding.json",
        data=json.dumps(defunding, indent=2), file_name="wallet_defunding.json")

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
