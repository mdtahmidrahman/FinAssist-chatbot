# FinAssist — AI-Powered Personal Finance Chatbot

### Built with **Streamlit**, **Gemini 2.5 Flash**, and **LangGraph**

FinAssist is a **specialized finance chatbot** designed to provide quick, practical advice on budgeting, savings, expenses, loans, and personal money management.
It is *not* a general-purpose AI — it only answers finance-related queries and politely declines all others.

---

## Features

* **Specialized Finance Advice Only**
  (budgeting, saving, expenses, loans, income planning)

* **Uses Google's Gemini 2.5 Flash Model(free)**
  for fast and efficient generation

* **Streamlit Frontend**
  clean UI for chatting

* **LangGraph Workflow**
  structured node-based processing using a `chat_node`

* **Automatic Input Filtering**
  rejects non-finance queries gracefully

* **Individual Chats**
  stores chats in threads using SQLite database

* **Restores Chats**
  restores all chats after re-run from the database

---

## Project Structure

```
project/
│── .env              # Environment file
│── app.py            # Main application file (Streamlit UI)
│── agent.py          # Backend (LangGraph)
│── README.md         # Documentation
```

---

## How It Works (High-Level)

### 1. User enters a question

→ Streamlit captures it from a text input box.

### 2. LangGraph processes the question

→ A node (`chat_node`) checks if the question is finance-related.

### 3. If valid, Gemini generates advice

→ Uses a structured finance-only prompt.

### 4. If invalid, the chatbot politely rejects

→ “Please ask something related to money management.”

### 5. Output is displayed on the UI

→ Streamlit updates the response area.

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mdtahmidrahman/FinAssist-chatbot.git
cd FinAssist-chatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows
```

### 3. Install Dependencies

```bash
pip install langchain langgraph langchain-google-genai langgraph-checkpoint-sqlite streamlit dotenv
```

### 4. Set the Gemini API Key

#### Windows

```bash
setx GEMINI_API_KEY "your_api_key_here"
```

#### Mac/Linux

```bash
export GEMINI_API_KEY="your_api_key_here"
```

---

## Running the App

```bash
streamlit run app.py
```

A browser window will open automatically.

---

# Code Explanation (Brief)

### **Finance Node Logic**

* Checks if the question contains finance keywords.
* If not → returns a polite refusal.
* If yes → sends a structured prompt to Gemini.

### **Gemini Model Call**

Uses:

```python
llm.invoke(messages)
```

### **LangGraph Workflow**

* One node (`chat_node`)
* Entry point = `chat_node`
* Compiled using:

```python
chatbot = graph.compile(checkpointer=checkpointer)
```

### **Streamlit UI**

* Title
* Text input
* Button
* Displays the answer on click
* Sidebar
* Chat History
* Chat Rename/Delete

---

## Example Queries

| User Question                         | Bot Response                  |
| ------------------------------------- | ----------------------------- |
| "How can I save 5000 taka per month?" | Gives saving tips             |
| "Should I take a personal loan?"      | Gives loan guidance           |
| "Tell me a poem."                     | Rejects — not finance-related |

---

## Future Improvements

* Add multi-step workflow (budget + goals)
* Include graphs (income vs expenses)
* Add authentication
* Expand domain rules for finance

---

## Technologies Used

| Component        | Technology       |
| ---------------- | ---------------- |
| Frontend         | Streamlit        |
| AI Model         | Gemini 2.5 Flash |
| Workflow         | LangGraph        |
| Backend Language | Python           |

---

