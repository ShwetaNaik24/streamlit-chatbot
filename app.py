import streamlit as st
import requests
import json
import csv
import pandas as pd
from datetime import datetime
from streamlit_mic_recorder import mic_recorder

# ---------------- SETTINGS ----------------

N8N_WEBHOOK = "https://shwetanaik24.app.n8n.cloud/webhook/ca5071d2-6190-438e-85ed-e4c77dfd8f3c/chat"

USERNAME = "admin"
PASSWORD = "1234"

LOG_FILE = "activity_log.csv"

# ---------------- LOG FUNCTION ----------------

def write_log(action, note=""):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), action, note])

# ---------------- LOGIN ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🔐 AI Assistant Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):

        if user == USERNAME and pwd == PASSWORD:
            st.session_state.logged_in = True
            write_log("Login", user)
            st.rerun()

        else:
            st.error("Invalid credentials")

    st.stop()

# ---------------- APP SETTINGS ----------------

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

st.title("🤖 AI Assistant")

write_log("App Opened")

# ---------------- SESSION ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- SIDEBAR ----------------

with st.sidebar:

    st.header("⚙ Controls")

    # Clear chat
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        write_log("Chat Cleared")
        st.rerun()

    # Logout
    if st.button("🚪 Logout"):
        write_log("Logout")
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")

    # Theme
    theme = st.selectbox("🎨 Theme", ["Light","Dark"])

    if theme == "Dark":
        st.markdown("""
        <style>
        body {background-color:#0E1117;color:white;}
        </style>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # AI Status
    st.subheader("🤖 AI Status")

    try:
        requests.get(N8N_WEBHOOK)
        st.success("AI Online")
    except:
        st.error("AI Offline")

    st.markdown("---")

    # Chat history
    st.header("💬 Chat History")

    if st.button("➕ New Chat"):
        if st.session_state.messages:
            st.session_state.history.append(st.session_state.messages)
        st.session_state.messages = []
        write_log("New Chat")
        st.rerun()

    for i, chat in enumerate(st.session_state.history):
        if st.button(f"Conversation {i+1}"):
            st.session_state.messages = chat
            st.rerun()

    st.markdown("---")

    # Search chat
    st.subheader("🔎 Search Chat")

    search = st.text_input("Search message")

    if search:
        for msg in st.session_state.messages:
            if search.lower() in msg["content"].lower():
                st.write(msg["content"])

    st.markdown("---")

    # Analytics
    st.subheader("📊 Chat Analytics")

    user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
    st.write("Questions asked:", len(user_msgs))

    st.markdown("---")

    # File upload
    uploaded_file = st.file_uploader("📎 Upload File", type=["txt","pdf","csv"])

    if uploaded_file:

        requests.post(
            N8N_WEBHOOK,
            files={"file": uploaded_file}
        )

        write_log("File Upload", uploaded_file.name)

        st.success("File sent to AI")

    st.markdown("---")

    # Download chat
    if st.session_state.messages:

        chat_text = ""

        for msg in st.session_state.messages:
            chat_text += f"{msg['role']}: {msg['content']}\n"

        st.download_button(
            "⬇ Download Chat",
            chat_text,
            file_name="chat.txt"
        )

    st.markdown("---")

    # Logs
    st.subheader("📜 Activity Logs")

    if st.button("View Logs"):

        try:
            logs = pd.read_csv(LOG_FILE, header=None)
            logs.columns = ["Time","Action","Notes"]
            st.dataframe(logs)
        except:
            st.warning("No logs yet")

    if st.button("⬇ Download Logs"):

        try:
            with open(LOG_FILE,"rb") as f:
                st.download_button(
                    "Download activity_log.csv",
                    f,
                    file_name="activity_log.csv"
                )
        except:
            st.warning("No log file")

    if st.button("🗑 Clear Logs"):

        open(LOG_FILE,"w").close()
        st.success("Logs cleared")

# ---------------- CHAT DISPLAY ----------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- VOICE INPUT ----------------

st.subheader("🎤 Voice Input")

audio = mic_recorder(
    start_prompt="Start Recording",
    stop_prompt="Stop Recording",
    key="recorder"
)

if audio:
    st.audio(audio["bytes"])

# ---------------- USER INPUT ----------------

prompt = st.chat_input("Type your message...")

if prompt:

    st.session_state.messages.append({
        "role":"user",
        "content":prompt
    })

    write_log("User Message", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    bot_reply = ""

    with st.chat_message("assistant"):

        placeholder = st.empty()
        placeholder.markdown("⏳ AI thinking...")

        try:

            response = requests.post(
                N8N_WEBHOOK,
                json={"chatInput":prompt}
            )

            for line in response.text.splitlines():

                try:
                    data = json.loads(line)

                    if data.get("type") == "item":

                        bot_reply += data.get("content","")
                        placeholder.markdown(bot_reply + "▌")

                except:
                    pass

        except Exception as e:

            bot_reply = f"⚠ Error: {e}"
            placeholder.markdown(bot_reply)

        placeholder.markdown(bot_reply)

    st.session_state.messages.append({
        "role":"assistant",
        "content":bot_reply
    })

    write_log("AI Response", bot_reply)
