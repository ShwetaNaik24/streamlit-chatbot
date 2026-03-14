import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# n8n webhook
N8N_WEBHOOK = "https://shwetanaik24.app.n8n.cloud/webhook/ca5071d2-6190-438e-85ed-e4c77dfd8f3c/chat"

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 AI Assistant")

# ---------------- LOG SYSTEM ----------------

if "logs" not in st.session_state:
    st.session_state.logs = []

def add_log(action):
    st.session_state.logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action
    })

# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.header("💬 Chat History")

    if st.button("➕ New Chat"):
        if st.session_state.messages:
            st.session_state.history.append(st.session_state.messages)
        st.session_state.messages = []
        add_log("New chat created")
        st.rerun()

    for i, chat in enumerate(st.session_state.history):
        if st.button(f"Conversation {i+1}"):
            st.session_state.messages = chat
            add_log(f"Opened conversation {i+1}")
            st.rerun()

    st.markdown("---")

    st.header("⚙ Controls")

    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        add_log("Chat cleared")
        st.rerun()

    # Download chat
    if st.session_state.messages:
        chat_text = ""
        for msg in st.session_state.messages:
            chat_text += f"{msg['role']}: {msg['content']}\n"

        st.download_button(
            "⬇ Download Chat",
            chat_text,
            file_name="chat_history.txt"
        )

    st.markdown("---")

    st.write("📊 Total messages:", len(st.session_state.messages))

    # File Upload
    uploaded_file = st.file_uploader("📎 Upload file", type=["txt","pdf","csv"])

    if uploaded_file:
        add_log(f"File uploaded: {uploaded_file.name}")

        response = requests.post(
            N8N_WEBHOOK,
            files={"file": uploaded_file}
        )

        st.success("File sent to AI!")

    st.markdown("---")

    # LOG VIEWER
    st.header("📜 Activity Logs")

    if st.session_state.logs:
        log_df = pd.DataFrame(st.session_state.logs)
        st.dataframe(log_df)

# ---------------- SHOW CHAT ----------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- USER INPUT ----------------

prompt = st.chat_input("Type your message...")

if prompt:

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    add_log("User sent message")

    with st.chat_message("user"):
        st.markdown(prompt)

    bot_reply = ""

    with st.chat_message("assistant"):

        placeholder = st.empty()
        placeholder.markdown("⏳ AI thinking...")

        try:

            response = requests.post(
                N8N_WEBHOOK,
                json={"chatInput": prompt}
            )

            for line in response.text.splitlines():
                try:
                    data = json.loads(line)
                    if data.get("type") == "item":
                        bot_reply += data.get("content", "")
                        placeholder.markdown(bot_reply)
                except:
                    pass

        except Exception as e:
            bot_reply = f"⚠ Error: {e}"

        placeholder.markdown(bot_reply)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply
    })

    add_log("AI response generated")
