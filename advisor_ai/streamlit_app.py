"""
Smart Academic Advisor — User Interface
Simple, clean, and chat-focused.
"""

import requests
import streamlit as st

# ── Configuration ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Smart Advisor",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"


def load_sessions(student_id):
    try:
        resp = requests.get(f"{API_URL}/sessions", params={"student_id": student_id})
        if resp.status_code != 200:
            return []
        payload = resp.json()
        if isinstance(payload, list):
            return payload
        return payload.get("sessions", [])
    except:
        return []

# ── Session State ───────────────────────────────────────────────────

if "student_id" not in st.session_state:
    st.session_state.student_id = "225241"

if "session_id" not in st.session_state:
    try:
        resp = requests.post(
            f"{API_URL}/sessions",
            json={"student_id": st.session_state.student_id},
        )
        st.session_state.session_id = resp.json().get("session_id", "")
    except:
        st.session_state.session_id = ""

if "messages" not in st.session_state:
    # Try to load history from backend
    try:
        resp = requests.get(
            f"{API_URL}/history",
            params={
                "student_id": st.session_state.student_id,
                "session_id": st.session_state.session_id,
            },
        )
        if resp.status_code == 200:
            history = resp.json().get("history", [])
            st.session_state.messages = history
        else:
            st.session_state.messages = []
    except:
        st.session_state.messages = []

# ── Sidebar: Admin & Settings ───────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings & Admin")

    # Session Management
    st.session_state.student_id = st.text_input("Student ID", value=st.session_state.student_id)
    sessions = load_sessions(st.session_state.student_id)
    session_options = [session["session_id"] for session in sessions]
    if st.session_state.session_id and st.session_state.session_id not in session_options:
        session_options.insert(0, st.session_state.session_id)

    if session_options:
        def session_label(session_id):
            for session in sessions:
                if session["session_id"] == session_id:
                    title = session.get("title") or "New chat"
                    return f"{title} ({session_id[:8]})"
            return session_id

        st.session_state.session_id = st.selectbox(
            "Sessions",
            options=session_options,
            index=session_options.index(st.session_state.session_id)
            if st.session_state.session_id in session_options
            else 0,
            format_func=session_label,
        )
        with st.expander("Sessions JSON"):
            st.json(sessions)
    else:
        st.info("No sessions yet.")
    
    if st.button("➕ New Chat"):
        try:
            resp = requests.post(
                f"{API_URL}/sessions",
                json={"student_id": st.session_state.student_id},
            )
            if resp.status_code == 200:
                st.session_state.session_id = resp.json()["session_id"]
                st.session_state.messages = []
                st.rerun()
        except:
            st.error("Backend offline")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset"):
            try:
                requests.post(
                    f"{API_URL}/chat",
                    json={
                        "student_id": st.session_state.student_id,
                        "session_id": st.session_state.session_id,
                        "message": "/start",
                    },
                )
                st.session_state.messages = []
                st.rerun()
            except:
                st.error("Backend offline")
    
    with col2:
        if st.button("📜 History"):
            try:
                resp = requests.get(
                    f"{API_URL}/history",
                    params={
                        "student_id": st.session_state.student_id,
                        "session_id": st.session_state.session_id,
                    },
                )
                if resp.status_code == 200:
                    st.session_state.messages = resp.json().get("history", [])
                    st.rerun()
            except:
                st.error("Failed to load")

    st.divider()

    # Admin Panel
    with st.expander("👮 Admin Tools"):
        st.subheader("Update Term")
        term = st.text_input("Active Term", value="Spring-2026")
        if st.button("Set Term"):
            try:
                resp = requests.post(f"{API_URL}/admin/set-term", json={"term": term})
                st.toast(resp.json().get("message", "Term updated"))
            except:
                st.error("Failed to set term")

        st.subheader("Upload Electives")
        text_data = st.text_area(
            "Courses",
            placeholder="Cloud Computing\nComputer Vision\nEthical Hacking",
            height=150
        )
        if st.button("Upload Electives"):
            electives = [
                item.strip().lstrip("-").strip()
                for line in text_data.splitlines()
                for item in line.split(",")
                if item.strip().lstrip("-").strip()
            ]
            try:
                resp = requests.post(
                    f"{API_URL}/admin/upload-electives",
                    json={"electives": electives},
                )
                st.toast(resp.json().get("message", "Uploaded"))
            except:
                st.error("Upload failed")

# ── Main Chat Interface ─────────────────────────────────────────────

st.title("🎓 Smart Academic Advisor")
st.caption("Ask about courses, regulations, electives, or get study support.")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    # 1. Add user message locally
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get response from API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            resp = requests.post(
                f"{API_URL}/chat", 
                json={
                    "student_id": st.session_state.student_id,
                    "session_id": st.session_state.session_id,
                    "message": prompt,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = data.get("response", "Sorry, I didn't get that.")
                message_placeholder.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                message_placeholder.markdown("❌ API Error")
        except requests.exceptions.ConnectionError:
            message_placeholder.markdown("❌ **Error:** Cannot connect to backend. Is `uvicorn` running?")
