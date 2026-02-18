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

# ── Session State ───────────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = "student-101"

if "messages" not in st.session_state:
    # Try to load history from backend
    try:
        resp = requests.get(f"{API_URL}/history", params={"session_id": st.session_state.session_id})
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
    st.session_state.session_id = st.text_input("Session ID", value=st.session_state.session_id)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset"):
            try:
                requests.post(f"{API_URL}/chat", json={"session_id": st.session_state.session_id, "message": "/start"})
                st.session_state.messages = []
                st.rerun()
            except:
                st.error("Backend offline")
    
    with col2:
        if st.button("📜 History"):
            try:
                resp = requests.get(f"{API_URL}/history", params={"session_id": st.session_state.session_id})
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
        upload_type = st.selectbox("Format", ["Text", "Excel/PDF/Image"])
        
        if upload_type == "Text":
            text_data = st.text_area(
                "Courses (comma-separated)",
                placeholder="Example: Cloud Computing, Computer Vision, Ethical Hacking\nOr paste a list:\n- Course A\n- Course B",
                height=150
            )
            if st.button("Upload Text"):
                try:
                    resp = requests.post(f"{API_URL}/admin/upload-electives", data={"text": text_data})
                    st.toast(resp.json().get("message", "Uploaded"))
                except:
                    st.error("Upload failed")
        else:
            file = st.file_uploader("Schedule File", type=["xlsx", "pdf", "png", "jpg"])
            if file and st.button("Upload File"):
                try:
                    files = {"file": (file.name, file.getvalue())}
                    resp = requests.post(f"{API_URL}/admin/upload-electives", files=files)
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
                json={"session_id": st.session_state.session_id, "message": prompt}
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

