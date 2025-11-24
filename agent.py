from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.pregel._checkpoint import empty_checkpoint, create_checkpoint
import os
from dotenv import load_dotenv
import sqlite3
import uuid

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.8,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

system_prompt = SystemMessage(content="""
You are FinAssist – a warm, caring, and expert personal finance advisor for Bangladesh.

You LOVE when people share their name, salary, job, or goals.
You always remember everything they tell you and reference it naturally.
You gently guide every conversation toward financial improvement.

Examples:
• "Hi, I'm Rahim" → "Nice to meet you, Rahim! How can I help with your money today?"
• "I earn 80k" → "Got it, Rahim! With 80k salary, you can easily save 15-20k per month. Want a plan?"
• "I'm a teacher" → "That's awesome! Teachers have great job security. Do you have an emergency fund yet?"

You ONLY talk about personal finance:
• Salary, budgeting, expenses
• Saving, emergency fund, goals
• Loans, EMI, debt
• Investments (FD, SIP, stocks, gold)
• Insurance, tax, retirement

If asked anything off-topic (politics, cricket, love, coding, health):
→ Politely refuse: "Sorry! I only know about money and finance. But I’d love to help you save, invest, or plan your future!"

Always be warm, encouraging, and pull the conversation back to finance.
""")

def chat_node(state: ChatState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [system_prompt] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# Setup SqliteSaver for persistent memory
conn = sqlite3.connect("chat_memory.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Compile with real persistent memory
chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_all_threads():
    """Get all active thread IDs from the checkpointer"""
    try:
        conn = sqlite3.connect("chat_memory.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT thread_id FROM checkpoints
            ORDER BY rowid DESC
        """)
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results if row[0]]
    except:
        return []


# === Export ===
__all__ = ["chatbot", "retrieve_all_threads"]


def create_thread(tid: str | None = None) -> str:
    tid = tid or str(uuid.uuid4())

    base = empty_checkpoint()
    cp = create_checkpoint(base, channels=None, step=0)
    config = {"configurable": {"thread_id": tid, "checkpoint_ns": ""}}
    metadata = {"source": "init", "step": 0, "parents": {}}

    checkpointer.put(config, cp, metadata, {})

    return tid

