"""
Search page — RAG-powered tender search.

UI only. All API calls go through api_client.py.
"""

import streamlit as st
from api_client import APIError, search_tenders

st.set_page_config(page_title="Search Tenders", page_icon="🔍", layout="wide")

st.title("🔍 Search Tenders")
st.caption("Ask anything about government tenders in plain English.")

# ── Session state — persists results across reruns ────────────────────────────
# Without this, results disappear every time the user interacts with the page.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of {role, content, citations}

# ── Example queries — helpful for demo/interview ──────────────────────────────
with st.expander("💡 Example questions"):
    examples = [
        "Show me road construction tenders in Delhi",
        "Which tenders close in the next 7 days?",
        "Find IT infrastructure tenders above 50 lakh",
        "List tenders from Maharashtra public works department",
    ]
    for example in examples:
        if st.button(example, key=example):
            st.session_state.prefill = example

# ── Chat input ─────────────────────────────────────────────────────────────────
question = st.chat_input(
    "Ask about tenders...",
    key="chat_input",
)

# Handle prefill from example buttons
if "prefill" in st.session_state:
    question = st.session_state.pop("prefill")

# ── Display chat history ───────────────────────────────────────────────────────
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant" and message.get("citations"):
            with st.expander(f"📄 Sources ({len(message['citations'])})"):
                for citation in message["citations"]:
                    st.caption(f"• {citation}")
            if message.get("confidence") is not None:
                st.progress(
                    message["confidence"],
                    text=f"Confidence: {message['confidence']:.0%}"
                )

# ── Handle new question ────────────────────────────────────────────────────────
if question and question.strip():
    # Show user message immediately
    with st.chat_message("user"):
        st.write(question)

    # Add to history
    st.session_state.chat_history.append({"role": "user", "content": question})

    # Call API with spinner
    with st.chat_message("assistant"):
        with st.spinner("Searching tenders and generating answer..."):
            try:
                result = search_tenders(question)

                answer = result.get("answer", "No answer returned.")
                citations = result.get("citations", [])
                confidence = result.get("confidence")

                st.write(answer)

                if citations:
                    with st.expander(f"📄 Sources ({len(citations)})"):
                        for citation in citations:
                            st.caption(f"• {citation}")

                if confidence is not None:
                    st.progress(confidence, text=f"Confidence: {confidence:.0%}")

                # Save to history so it persists
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "citations": citations,
                    "confidence": confidence,
                })

            except APIError as e:
                st.error(f"Error {e.status_code}: {e.detail}")

# ── Clear history button ───────────────────────────────────────────────────────
if st.session_state.chat_history:
    if st.button("🗑️ Clear conversation", type="secondary"):
        st.session_state.chat_history = []
        st.rerun()
