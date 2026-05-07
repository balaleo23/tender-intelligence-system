"""
Tender Intelligence — Streamlit entry point.

This file is the landing page only.
Actual features live in pages/ (Streamlit multi-page routing).

When migrating to React/Next.js:
  - Delete this file and pages/
  - Keep api_client.py as reference for API contract
  - Build React components that call the same endpoints
"""

import streamlit as st
from api_client import APIError, health_check

# ── Page config — must be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="Tender Intelligence",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📋 Tender Intelligence System")
st.caption("RAG-powered search over Indian government tenders from eprocure.gov.in")

st.divider()

# ── System health — shown on landing page ─────────────────────────────────────
st.subheader("System Status")

try:
    health = health_check()

    col1, col2, col3, col4 = st.columns(4)

    def status_icon(value: str) -> str:
        return "🟢" if value.lower() == "ok" else "🔴"

    col1.metric("API", f"{status_icon(health.get('status', 'error'))} {health.get('status', 'error').upper()}")
    col2.metric("Postgres", f"{status_icon(health.get('postgres', 'error'))} {health.get('postgres', 'error').upper()}")
    col3.metric("Qdrant", f"{status_icon(health.get('qdrant', 'error'))} {health.get('qdrant', 'error').upper()}")
    col4.metric("Ollama", f"{status_icon(health.get('ollama', 'error'))} {health.get('ollama', 'error').upper()}")

except APIError as e:
    st.error(f"⚠️ Cannot reach backend: {e.detail}")
    st.info("Make sure the API is running: `uvicorn ingestion_engine.api.app:app --reload`")

st.divider()

# ── Navigation guide ───────────────────────────────────────────────────────────
st.subheader("Get Started")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 🔍 Search\nAsk questions about tenders using natural language. Powered by RAG.")

with col2:
    st.info("### 📥 Ingest\nLoad tender data from local JSON files into the vector database.")

with col3:
    st.info("### 🕷️ Scrape\nTrigger a live scrape from eprocure.gov.in to fetch latest tenders.")

st.caption("Use the sidebar to navigate between pages.")
