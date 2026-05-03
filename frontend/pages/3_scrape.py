"""
Scrape page — triggers scraper and polls for status every 5 seconds.
UI only. All API calls go through api_client.py.
"""

import time

import streamlit as st
from api_client import APIError, get_scrape_status, trigger_scrape

st.set_page_config(page_title="Scrape Tenders", page_icon="🕷️", layout="wide")

st.title("🕷️ Scrape Live Tenders")
st.caption("Trigger the Playwright scraper to fetch latest tenders from eprocure.gov.in.")

# ── Session state ─────────────────────────────────────────────────────────────
if "scrape_triggered" not in st.session_state:
    st.session_state.scrape_triggered = False

# ── Current status from API ───────────────────────────────────────────────────
try:
    status = get_scrape_status()
    state = status.get("state", "idle")
except APIError as e:
    st.error(f"Cannot reach API: {e.detail}")
    st.stop()

# ── Status display ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

state_display = {
    "idle":    ("⚪", "Idle",    None),
    "running": ("🟡", "Running", "normal"),
    "done":    ("🟢", "Done",    None),
    "failed":  ("🔴", "Failed",  None),
}
icon, label, _ = state_display.get(state, ("⚪", "Unknown", None))

col1.metric("Status", f"{icon} {label}")
col2.metric("Tenders Scraped", status.get("tenders_scraped", 0))
col3.metric("Started", status.get("started_at", "—") or "—")

st.divider()

# ── Running state — auto-refresh ───────────────────────────────────────────────
if state == "running":
    st.warning("⏳ Scraping in progress... page refreshes every 5 seconds.")
    with st.spinner("Scraper is running — fetching tenders from eprocure.gov.in..."):
        time.sleep(5)   # wait 5 seconds then rerun to poll latest status
    st.rerun()

# ── Done state ─────────────────────────────────────────────────────────────────
elif state == "done":
    st.success(
        f"✅ Scraping complete — **{status.get('tenders_scraped', 0)}** tenders downloaded. "
        "Go to **📥 Ingest** to index them into the database."
    )
    if status.get("finished_at"):
        st.caption(f"Finished at: {status['finished_at']}")

# ── Failed state ───────────────────────────────────────────────────────────────
elif state == "failed":
    st.error(f"❌ Scraping failed: {status.get('error', 'Unknown error')}")
    st.caption("Fix the error and try again.")

# ── Idle / done / failed — show trigger button ────────────────────────────────
if state in ("idle", "done", "failed"):
    st.divider()

    with st.expander("ℹ️ What the scraper does"):
        st.markdown("""
        1. Opens a headless Chromium browser (Playwright)
        2. Navigates to **eprocure.gov.in**
        3. Filters tenders closing within **14 days**
        4. Downloads tender PDFs → saves to `data/tenders/`
        5. Saves metadata JSON → `meta_data/`
        6. After scraping → run **📥 Ingest** to index them
        """)

    st.warning("⏱️ Scraping takes **3–10 minutes**. The page will auto-refresh every 5 seconds.")

    if st.button("🕷️ Start Scraping", type="primary", use_container_width=False):
        try:
            trigger_scrape()
            st.session_state.scrape_triggered = True
            st.rerun()   # rerun immediately to show running state
        except APIError as e:
            if e.status_code == 409:
                # Another scrape already running — just show status
                st.warning("A scrape is already running. Showing live status...")
                st.rerun()
            else:
                st.error(f"Failed to start scraper ({e.status_code}): {e.detail}")
