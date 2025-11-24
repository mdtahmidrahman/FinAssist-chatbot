from venv import logger
import streamlit as st
from agent import chatbot, retrieve_all_threads, create_thread
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import time
import sqlite3

st.set_page_config(page_title="FinAssist", page_icon="💰", layout="centered")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "thread_names" not in st.session_state:
    st.session_state.thread_names = {}

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = retrieve_all_threads()

def get_thread_name(tid: str) -> str:
    if tid in st.session_state.thread_names:
        return st.session_state.thread_names[tid]
    try:
        conn = sqlite3.connect("chat_memory.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checkpoint FROM checkpoints 
            WHERE thread_id = ? 
            ORDER BY rowid ASC LIMIT 1
        """, (tid,))
        row = cursor.fetchone()
        conn.close()
        if row:
            import json
            state = json.loads(row[0])
            messages = state.get("channel_values", {}).get("messages", [])
            for msg in messages:
                if msg.get("type") == "human":
                    text = msg["content"][:40]
                    return text + ("..." if len(msg["content"]) > 40 else "")
    except:
        pass
    return "New Chat"

def set_thread_name(tid: str, name: str):
    st.session_state.thread_names[tid] = name.strip() or "New Chat barro"

def create_new_thread():
    new_id = str(uuid.uuid4())
    try:
        create_thread(new_id)
    except Exception:
        pass
    st.session_state.thread_id = new_id
    st.session_state.thread_names[new_id] = "New Chat"
    st.session_state.chat_threads = [new_id] + [t for t in st.session_state.chat_threads if t != new_id]
    st.rerun()


with st.sidebar:
    st.title("FinAssist")
    st.caption("Your Personal Finance AI for Bangladesh")

    if st.button("New Chat", type="primary", use_container_width=True):
        create_new_thread()

    st.markdown("### Your Chats")

    if st.button("Refresh List", use_container_width=True):
        st.session_state.chat_threads = retrieve_all_threads()
        st.rerun()

    for tid in st.session_state.chat_threads[:30]:
        name = get_thread_name(tid)

        col1, col2, col3 = st.columns([3.8, 1, 1])

        with col1:
            if st.button(name, key=f"select_{tid}", use_container_width=True):
                st.session_state.thread_id = tid
                st.rerun()

        with col2:
            if st.button("✏️", key=f"edit_{tid}"):
                st.session_state.editing = tid
                st.rerun()

        with col3:
            if st.button("❌", key=f"del_{tid}"):
                st.session_state.confirm_delete = tid
                st.rerun()

    if st.session_state.get("editing"):
        tid = st.session_state.editing
        current = get_thread_name(tid)
        new_name = st.text_input("Rename chat", value=current, key=f"name_{tid}")
        c1, c2 = st.columns(2)
        if c1.button("Save", key=f"save_{tid}"):
            set_thread_name(tid, new_name)
            del st.session_state.editing
            st.success("Renamed!")
            time.sleep(0.6)
            st.rerun()
        if c2.button("Cancel"):
            del st.session_state.editing
            st.rerun()

    if st.session_state.get("confirm_delete"):
        tid = st.session_state.confirm_delete
        st.error(f"Delete “{get_thread_name(tid)}”? This cannot be undone.")
        c1, c2 = st.columns(2)
        if c1.button("Yes, Delete Forever", type="primary"):
            conn = sqlite3.connect("chat_memory.db")
            conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (tid,))
            conn.commit()
            conn.close()

            st.session_state.chat_threads = [t for t in st.session_state.chat_threads if t != tid]
            st.session_state.thread_names.pop(tid, None)
            if st.session_state.thread_id == tid:
                st.session_state.thread_id = None

            del st.session_state.confirm_delete
            st.success("Chat deleted")
            time.sleep(0.8)
            st.rerun()
        if c2.button("Cancel"):
            del st.session_state.confirm_delete
            st.rerun()

current_thread = st.session_state.thread_id

if not current_thread:
    st.markdown(
        """
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="font-size: 4.5rem; margin-bottom: 10px;">
                FinAssist
            </h1>
            <p style="font-size: 1.6rem; color: #64748b; max-width: 700px; margin: 30px auto;">
                Your personal finance advisor in Bangladesh.<br>
            </p>
            <div style="margin-top: 60px;">
                <p style="color: #94a3b8; font-size: 1.2rem;">
                    Click <strong>“New Chat”</strong> to start talking about your money
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # ACTIVE CHAT
    st.title("Chat")
    st.caption(get_thread_name(current_thread))

    try:
        config = {"configurable": {"thread_id": current_thread}}
        state = chatbot.get_state(config) 
        messages = state.values.get("messages", []) if state else []
    except Exception as e:
        logger.error(f"Failed to load state for thread {current_thread}: {e}")
        messages = []
        st.error("Could not load this chat.")

    for msg in messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(msg.content)

    # Chat input
    if prompt := st.chat_input("Tell me your name, salary, or ask about money..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            stream_config = {
                "configurable": {"thread_id": current_thread},
                "stream_mode": "messages"
            }

            try:
                stream_iter = chatbot.stream(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=stream_config,
                    stream_mode="messages"
                )
            except TypeError:
                # Fallback if chatbot.stream signature differs
                stream_iter = chatbot.stream({"messages": [HumanMessage(content=prompt)]})

            for item in stream_iter:
                if isinstance(item, tuple) and len(item) >= 1:
                    chunk = item[0]
                else:
                    chunk = item

                # Extract content
                content_part = None
                if hasattr(chunk, "content"):
                    content_part = getattr(chunk, "content")
                elif isinstance(chunk, dict) and "content" in chunk:
                    content_part = chunk["content"]
                elif isinstance(chunk, str):
                    content_part = chunk

                if content_part:
                    full_response += content_part
                    placeholder.markdown(full_response + "▌")
                    time.sleep(0.02)

            placeholder.markdown(full_response)

        # Refresh thread list and possibly rename
        st.session_state.chat_threads = retrieve_all_threads()
        if get_thread_name(current_thread) == "New Chat":
            short = prompt[:40] + ("..." if len(prompt) > 40 else "")
            set_thread_name(current_thread, short)

# === Footer ===
st.markdown("---")
st.caption("Powered by Gemini 2.5 Flash")
