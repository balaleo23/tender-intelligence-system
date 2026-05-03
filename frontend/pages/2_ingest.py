"""
Ingest page — trigger the data ingestion pipeline.
UI only. All API calls go through api_client.py.
"""

import streamlit as st
from api_client import APIError, list_tenders, trigger_ingestion

st.set_page_config(page_title="Ingest Data", page_icon="📥", layout="wide")

st.title("📥 Ingest Tender Data")
st.caption("Load tender metadata from JSON files into Postgres and Qdrant.")

# ── Explain what this does ─────────────────────────────────────────────────────
with st.expander("ℹ️ How ingestion works"):
    st.markdown("""
    1. Reads `Tender_data_*.json` and `Tenders_filepath_*.json` from the `meta_data/` folder
    2. Saves tender metadata into **Postgres**
    3. Extracts text from PDF documents
    4. Chunks text → generates embeddings → upserts into **Qdrant**

    Run this after scraping or adding new JSON files manually.
    """)

st.divider()

# ── Trigger ingestion ──────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 3])

with col1:
    run_ingestion = st.button("▶️ Run Ingestion", type="primary", use_container_width=True)

with col2:
    st.caption("This may take several minutes depending on the number of tenders and PDFs.")

if run_ingestion:
    with st.spinner("Running ingestion pipeline... this may take a few minutes."):
        try:
            result = trigger_ingestion()
            st.success(f"✅ {result['message']} — **{result['tenders_processed']}** tenders processed.")
        except APIError as e:
            st.error(f"Ingestion failed ({e.status_code}): {e.detail}")

st.divider()

# ── Current tenders in DB ──────────────────────────────────────────────────────
st.subheader("Tenders in Database")

if st.button("🔄 Refresh list"):
    st.rerun()

try:
    tenders = list_tenders()

    if not tenders:
        st.info("No tenders in the database yet. Run ingestion first.")
    else:
        st.caption(f"**{len(tenders)}** tenders indexed")
        st.dataframe(
            tenders,
            use_container_width=True,
            column_config={
                "tender_uid": st.column_config.TextColumn("UID", width="small"),
                "title": st.column_config.TextColumn("Title", width="large"),
                "organization": st.column_config.TextColumn("Organisation"),
                "published_date": st.column_config.DatetimeColumn("Published", format="DD MMM YYYY"),
                "bid_submission_end_date": st.column_config.DatetimeColumn("Closes", format="DD MMM YYYY"),
            },
        )

except APIError as e:
    st.error(f"Could not load tenders: {e.detail}")
