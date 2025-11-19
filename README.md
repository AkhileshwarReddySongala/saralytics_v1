# Saralytics: The AI-Powered Business Analytics Dashboard

**Submission for the Kaggle 5-Day AI Agents Intensive Course Capstone Project**

**Video Demo:** [https://www.youtube.com/your-video-link-here](https://www.youtube.com/your-video-link-here)

---

## 1. Introduction

### The Problem: The Data-Insight Gap
In today's data-rich world, businesses, especially in sectors like retail and distribution, collect vast amounts of transactional data. However, this data often remains locked away in legacy databases, inaccessible to the non-technical decision-makers who need it most. Getting specific, role-relevant insights—like a sales manager tracking team performance or a finance analyst investigating product profitability—is a slow and inefficient process, requiring data analysts to act as manual intermediaries for every query. This "data-insight gap" delays critical business decisions and hinders agility.

### The Solution: A Team of Specialized AI Agents
Saralytics is a web-based business analytics dashboard that bridges this gap. It provides a real-time, interactive view of a company's sales and inventory data. Its core innovation lies in its **hierarchical multi-agent system**, a team of specialized AI agents designed to mimic a real-world analytics department:

*   **Mandy (The Manager Agent):** A top-level orchestrator powered by **Google's Gemini model**. Mandy's sole job is to receive the user's request and intelligently delegate it to the correct specialist.
*   **Sam (The Sales Agent):** A specialist focused on revenue, sales trends, and top-selling products.
*   **Ivy (The Inventory Agent):** A specialist focused on stock movement, unit counts, and product specifications.
*   **Finn (The Finance Agent):** A specialist in profitability, equipped with a **custom tool** to perform precise profit margin calculations directly from the database.

Users interact with Saralytics through a single, conversational chat interface. The system feels like talking to one unified AI, but behind the scenes, Mandy ensures the right expert is always on the job.

### The Value: Democratizing Data, Accelerating Decisions
Saralytics democratizes data analysis. It transforms the process from a slow, ticket-based system into an interactive, instantaneous conversation.

*   **For Stakeholders:** Empowers non-technical users to perform complex data queries on their own, reducing time-to-insight from days to seconds.
*   **For Data Analysts:** Frees up valuable data analyst time from routine queries, allowing them to focus on more strategic, deep-dive analyses.
*   **For the Business:** Fosters a data-driven culture by making insights accessible to everyone, leading to faster, more informed, and more profitable business decisions.

---

## 2. Implementation

### Architecture
Saralytics is built on a modern, full-stack architecture designed for robust performance and modularity. The agentic system is hierarchical, with a manager agent routing tasks to a team of subordinate specialist agents.

*   **Frontend:** Built with vanilla **HTML, CSS, and JavaScript**. It uses **Chart.js** for interactive data visualizations and **Marked.js** to render the AI's markdown responses into clean HTML. The frontend communicates with the backend via asynchronous API calls, including a streaming connection for real-time AI responses.
*   **Backend:** A powerful **Django** application serves as the core of the project. It handles API routing, database connections, and orchestrates the multi-agent system.
*   **Database:** Connects directly to a legacy **Microsoft Access Database (`.MDB`)** using `pyodbc` and `pandas`, demonstrating the ability to integrate with existing enterprise systems.
*   **AI Models:** A hybrid model approach is used:
    *   The **Manager Agent (Mandy)** is powered by **Google's Gemini Pro** for fast and accurate task routing.
    *   The **Specialist Agents (Sam, Ivy, Finn)** are powered by a larger, locally-hosted model (`gpt-oss:120b-cloud` via **Ollama**) for deep, analytical reasoning.
*   **Multi-Agent System:** The core logic resides in two chained Django views that create the agent hierarchy. The `manager_agent_api` receives the user request and uses Gemini to choose an agent. It then simulates a new request to the `specialist_agent_api`, which executes the full "reason-act" loop for the chosen specialist.

![Saralytics Architecture Diagram](architecture.png)

### Technical Features Showcase
This project successfully implements **five (5)** of the key concepts from the course:

1.  ✅ **Multi-agent system:** The hierarchical system with a Gemini-powered Manager delegating to parallel specialist agents is a core feature. Each specialist has a unique persona and sandboxed data access, ensuring their responses are expert and relevant.

2.  ✅ **Agent powered by an LLM:** The project demonstrates a sophisticated hybrid approach, using **Gemini** for fast classification/routing and a larger **Ollama-hosted model** for in-depth analysis.

3.  ✅ **Custom Tools:** The Finance Agent, Finn, has access to a custom-built Python tool, `get_profit_analysis_for_item()`. The agent demonstrates a full "reason-act" loop: it reasons that a tool is needed, formulates a JSON call, the backend executes the tool against the database, and the result is fed back to the agent for final synthesis.

4.  ✅ **Sessions & Memory:** The chat interface maintains a session history. The conversation history is sent back to the agent with each new question, providing crucial context. This allows for natural, multi-turn conversations where the user can ask follow-up questions, and the agent "remembers" the subject of the previous turn.

5.  ✅ **Observability (Logging/Tracing):** The entire agentic workflow, from the manager's decision to the specialist's tool use, is printed to the Django console with clear labels. This provides a detailed trace of the system's "thoughts" and actions, which is invaluable for debugging and understanding agent behavior.

### Setup and Installation
1.  **Clone the repository:** `git clone https://github.com/AkhileshwarReddySongala/saralytics.git`
2.  **Prerequisites:**
    *   Python 3.11+
    *   Windows Operating System
    *   Microsoft Access Database Engine 2016 Redistributable (ensure it matches your Python's bitness - 64-bit is common).
    *   Ollama installed and running locally.
3.  **Setup Virtual Environment:**
    ```bash
    cd your-repo-name
    python -m venv venv
    .\venv\Scripts\activate
    ```
4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Configure API Key:**
    *   Create a file named `.env` in the root of the project.
    *   Add your Google AI Studio API key to it: `GEMINI_API_KEY="YOUR_API_KEY_HERE"`
6.  **Database:** Place your Microsoft Access database file (e.g., `MRF.MDB`) in the root of the project directory. If your filename or table names are different, update them in `dashboard/views.py`. *(Note: The database file is not included in this repository for data privacy reasons.)*
7.  **Run the Django Server:**
    ```bash
    python manage.py runserver
    ```
8.  Access the application at `http://127.0.0.1:8000/`.

---

## 3. Bonus Points

*   **Effective Use of Gemini (5 points):** The project strategically uses the Gemini Pro model to power the high-level Manager Agent ("Mandy"), handling the critical task of routing user intent to the correct specialist. This demonstrates a practical and efficient use of the model for classification tasks within a larger agentic system.
