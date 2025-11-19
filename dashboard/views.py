# dashboard/views.py
# Final version for Kaggle AI Agents Capstone Submission
# Project: Saralytics - AI-Powered Business Analytics Dashboard

# --- Core Django and Python Libraries ---
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse, HttpRequest
import os
import json

# --- Third-Party Libraries ---
import pyodbc  # For connecting to the MS Access database
import pandas as pd  # For data manipulation and analysis
import requests  # For making HTTP requests to the Ollama and Gemini APIs
from dotenv import load_dotenv  # For securely managing API keys
import google.generativeai as genai  # The Google Gemini client library


# ===================================================================
# INITIAL CONFIGURATION
# This section sets up the necessary API clients and environment variables.
# ===================================================================

# Load environment variables from a .env file in the project root.
# This is a security best practice to keep API keys out of the source code.
load_dotenv()

# Configure the Google Gemini client using the API key from the .env file.
# This is required for our Manager Agent to function.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("\n[CONFIG] Gemini API configured successfully.")
else:
    # Provides a clear warning if the key is missing, ensuring graceful failure.
    print("\n[CONFIG] WARNING: GEMINI_API_KEY not found in .env file. Manager Agent will be disabled.")

# ===================================================================
# HELPER FUNCTIONS & DATA-FACING APIS
# These functions handle direct interactions with the database and serve data to the frontend charts.
# ===================================================================

# --- Database Connection Helper ---
def get_data_from_db(sql_query, params=None):
    """
    Connects to the MS Access database, executes a given SQL query, and returns the result as a pandas DataFrame.
    This function centralizes all database interactions.
    Args:
        sql_query (str): The SQL query to execute.
        params (list, optional): A list of parameters for the SQL query to prevent SQL injection.
    Returns:
        pd.DataFrame: A pandas DataFrame containing the query results, or an empty DataFrame on error.
    """
    db_file_path = os.path.join(settings.BASE_DIR, 'MRF.MDB')
    if not os.path.exists(db_file_path):
        print(f"[ERROR] Database file not found at {db_file_path}")
        return pd.DataFrame()
    
    CONN_STR = (r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' + r'DBQ=' + db_file_path + r';')
    try:
        cnxn = pyodbc.connect(CONN_STR)
        # Using read_sql with the 'params' argument is a security measure against SQL injection.
        dataframe = pd.read_sql(sql_query, cnxn, params=params)
        cnxn.close()
        return dataframe
    except Exception as e:
        print(f"[ERROR] Database fetch error: {e}")
        return pd.DataFrame()

# --- Main View & Chart APIs ---
# These views are simple data endpoints for the frontend visualizations.
def home(request): return render(request, 'dashboard/index.html')

def sales_over_time_api(request):
    sql = "SELECT DOCDT, TOTALITEMVALUE FROM SALEINVOICE"
    df = get_data_from_db(sql)
    if df.empty: return JsonResponse({"error": "Data not available."})
    df['DOCDT'] = pd.to_datetime(df['DOCDT'])
    monthly_sales = df.set_index('DOCDT').resample('ME')['TOTALITEMVALUE'].sum()
    output = { "labels": monthly_sales.index.strftime('%Y-%m').tolist(), "data": monthly_sales.values.tolist() }
    return JsonResponse(output)

def sales_by_item_api(request):
    sql = "SELECT ITEMNAME, TOTALITEMVALUE FROM SALEINVOICE"
    df = get_data_from_db(sql)
    if df.empty: return JsonResponse({"error": "Data not available."})
    item_sales = df.groupby('ITEMNAME')['TOTALITEMVALUE'].sum().sort_values(ascending=False).head(15)
    output = { "labels": item_sales.index.tolist(), "data": item_sales.values.tolist() }
    return JsonResponse(output)

def quantity_by_size_api(request):
    sql = "SELECT ITEMSIZE, QUANTITY FROM SALEINVOICE"
    df = get_data_from_db(sql)
    if df.empty: return JsonResponse({"error": "Data not available."})
    size_quantity = df.groupby('ITEMSIZE')['QUANTITY'].sum().sort_values(ascending=False).head(15)
    output = { "labels": size_quantity.index.tolist(), "data": size_quantity.values.tolist() }
    return JsonResponse(output)


# ===================================================================
# AI AGENT CORE LOGIC
# This section contains the implementation of the multi-agent system.
# ===================================================================

# --- Streaming Helper for Ollama ---
def stream_ollama_response(payload):
    """
    A generator function that connects to the local Ollama service and streams the response.
    This allows the frontend to display the AI's answer token-by-token.
    Args:
        payload (dict): The data to send to the Ollama API, including the model and prompt.
    Yields:
        str: A chunk of the AI's response text.
    """
    ollama_url = 'http://localhost:11434/api/generate'
    try:
        # 'stream=True' is critical for enabling streaming responses.
        with requests.post(ollama_url, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()
            # Ollama streams back newline-delimited JSON objects.
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    # We yield only the 'response' part, which is the text token.
                    yield chunk.get('response', '')
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ollama streaming error: {e}")
        yield "Error: Could not connect to the Ollama service. Please ensure it is running."

# --- Custom Profit Tool (Feature Showcase: Custom Tools) ---
def get_profit_analysis_for_item(item_name: str) -> dict:
    """
    A custom tool for the Finance Agent. It performs a precise, deterministic calculation
    that the LLM cannot do on its own, ensuring data accuracy.
    Args:
        item_name (str): The name of the item to analyze.
    Returns:
        dict: A dictionary containing the calculated profit metrics.
    """
    print(f"\n[TOOL] --- Executing Tool: get_profit_analysis_for_item ---")
    print(f"[TOOL] Parameter: item_name = '{item_name}'")
    sql = "SELECT TOTALITEMVALUE, MCODE FROM SALEINVOICE WHERE ITEMNAME = ?"
    df = get_data_from_db(sql, params=[item_name])
    if df.empty:
        result = {"error": f"No data found for item '{item_name}'."}
        print(f"[TOOL] Result: {result}")
        return result
    
    # Perform calculations using pandas for accuracy.
    total_revenue = df['TOTALITEMVALUE'].sum()
    total_profit = df['MCODE'].sum()
    profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
    
    result = {
        "currency": "INR", "item_name": item_name, "total_revenue": f"₹{total_revenue:,.2f}",
        "total_profit": f"₹{total_profit:,.2f}", "number_of_sales": len(df),
        "profit_margin_percent": f"{profit_margin:.2f}%"
    }
    print(f"[TOOL] Result: {json.dumps(result)}")
    return result

# --- Specialist Agent Worker Function (Feature Showcase: Multi-agent System) ---
def specialist_agent_api(request):
    """
    This function is the "worker" that executes the logic for a specific specialist agent
    (Sam, Ivy, or Finn) once chosen by the manager. It contains the full agentic loop for tool use.
    """
    try:
        body = json.loads(request.body)
        question = body.get('question', '')
        agent = body.get('agent') # Provided by the manager agent
        history = body.get('history', []) 
        
        print(f"\n[AGENT] --- Specialist Agent Activated: {agent.upper()} ---")
        
        # This dictionary acts as a router to select the agent's persona and data access.
        agent_configs = {
            "sales": { "persona": "You are 'Sam', a Sales Analyst for a tyre company in India. Answer questions about sales trends, revenue, and top products. Format your response in GitHub-flavored Markdown.", "sql_query": "SELECT DOCDT, ITEMNAME, QUANTITY, TOTALITEMVALUE FROM SALEINVOICE"},
            "inventory": { "persona": "You are 'Ivy', an Inventory Analyst for a tyre company in India. Answer questions about stock movement, product sizes, and unit counts. Format your response in GitHub-flavored Markdown.", "sql_query": "SELECT ITEMNAME, ITEMSIZE, QUANTITY FROM SALEINVOICE"},
            "finance": {
                "persona": """You are 'Finn', a meticulous Finance Analyst for a tyre company in India. All currency is in Indian Rupees (INR).


                **CRITICAL DOMAIN KNOWLEDGE:**

                The database table you have access to contains a column named `MCODE`. **`MCODE` represents the total profit in Rupees for each sale transaction.** Your primary role is to answer questions about profitability using this `MCODE` column. The `DOCDT` column contains the date of each transaction.


                **IMPORTANT TOOL AVAILABLE:**

                You have a special tool: `get_profit_analysis_for_item(item_name: str)`.

                - This tool provides a precise profit breakdown for a SINGLE item.

                - You MUST use this tool whenever a user asks for profit, profit margin, or a detailed financial summary of a specific, named item.

                - To use the tool, respond with ONLY the following JSON and nothing else:
                {"tool_name": "get_profit_analysis_for_item", "parameters": {"item_name": "THE_ITEM_NAME_HERE"}}

                If the user's question is general and does not name a specific item (e.g., "summarize all profit"), answer based on the sample data provided below. Do NOT use the tool for general questions.""",
                "sql_query": "SELECT DOCDT, ITEMNAME, TOTALITEMVALUE, MCODE FROM SALEINVOICE"
            }
        }
        config = agent_configs.get(agent)
        
        # Each agent gets a fresh, role-relevant data sample for every query.
        df = get_data_from_db(config['sql_query'])
        data_context = df.sample(n=min(len(df), 50)).to_markdown(index=False)
        history_str = "\n".join([f"Previous Q: {msg['content']}" if msg['role'] == 'user' else f"Your Previous A: {msg['content']}" for msg in history])
        
        initial_prompt = f"""{config['persona']}\n\nCONVERSATION HISTORY:\n{history_str}\n\nDATA SAMPLE:\n{data_context}\n\nEvaluate the user's new question and decide whether to use a tool or answer directly. User's new question: "{question}" """

        # --- Agentic Loop (Reasoning Step) ---
        ollama_url = 'http://localhost:11434/api/generate'
        # 'format: "json"' prompts the LLM to structure its decision, enabling tool use.
        payload = {"model": "gpt-oss:120b-cloud", "prompt": initial_prompt, "stream": False, "format": "json"}
        
        print(f"[AGENT] Sending initial prompt to Ollama for '{agent}' to make a decision.")
        response = requests.post(ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        agent_response_str = response.json().get('response', '{}')
        
        print(f"[AGENT] Ollama Decision (raw): {agent_response_str}")

        agent_decision = None
        try:
            agent_decision = json.loads(agent_response_str)
        except json.JSONDecodeError: pass # Not a JSON response, so it's a direct answer.

        # --- Agentic Loop (Action Step) ---
        # Check if the agent's decision is to use our specific, defined tool.
        if isinstance(agent_decision, dict) and agent_decision.get("tool_name") == "get_profit_analysis_for_item":
            print(f"[AGENT] Decision: USE TOOL 'get_profit_analysis_for_item'.")
            item_name = agent_decision.get("parameters", {}).get("item_name")
            if item_name:
                # Execute the tool and get a structured result.
                tool_result = get_profit_analysis_for_item(item_name)
                # Formulate a new prompt, feeding the tool's result back to the agent for synthesis.
                second_prompt = f"""You are 'Finn', the Finance Analyst. You used your tool for '{item_name}' and got this result: {json.dumps(tool_result)}. Now, provide a final, user-friendly answer to the original question: "{question}". Summarize the findings clearly in Markdown."""
                
                print(f"[AGENT] Sending second prompt to Ollama with tool result.")
                final_payload = {"model": "gpt-oss:120b-cloud", "prompt": second_prompt, "stream": True}
                return StreamingHttpResponse(stream_ollama_response(final_payload), content_type="text/plain")
        
        # If the agent did not decide to use a tool, it must be a direct answer.
        print(f"[AGENT] Decision: ANSWER DIRECTLY without using a tool.")
        final_payload = {"model": "gpt-oss:120b-cloud", "prompt": initial_prompt, "stream": True}
        return StreamingHttpResponse(stream_ollama_response(final_payload), content_type="text/plain")

    except Exception as e:
        print(f"[ERROR] An error occurred in specialist_agent_api: {e}")
        def error_stream(): yield f"Error in specialist agent: {e}"
        return StreamingHttpResponse(error_stream(), status=500, content_type="text/plain")

# --- Manager Agent API (Main Entry Point / Feature Showcase: Gemini Use) ---
def manager_agent_api(request):
    """
    The main entry point for the chat. It acts as an orchestrator, using the Gemini model
    to intelligently route the user's question to the correct specialist agent.
    This creates a two-layer agent hierarchy.
    """
    print("\n\n[MANAGER] <<<< New Request Received >>>>")
    try:
        body = json.loads(request.body)
        question = body.get('question', '')
        history = body.get('history', [])
        print(f"[MANAGER] User Question: '{question}'")
        if not question: return JsonResponse({'error': 'No question provided.'}, status=400)
    except json.JSONDecodeError: return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    if not GEMINI_API_KEY:
        print("[ERROR] Manager Agent cannot function without a Gemini API Key.")
        def error_stream(): yield "Error: The Manager Agent is not configured on the server."
        return StreamingHttpResponse(error_stream(), status=500, content_type="text/plain")

    # The prompt for the manager is simple: its only job is to classify the user's intent.
    manager_prompt = f"""You are "Mandy", the Manager Agent. Your job is to delegate a user's question to ONE of the following specialists: "sales", "inventory", or "finance". Respond with ONLY a single word.
- "sales": For questions about sales, revenue trends, top products, dates.
- "inventory": For questions about stock, unit counts, product sizes.
- "finance": For questions about profit, profit margins, financial analysis.
Conversation History: {json.dumps(history)}
User's New Question: "{question}" """
    
    try:
        print("[MANAGER] Asking Gemini to choose a specialist...")
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(manager_prompt)
        chosen_agent = response.text.strip().lower().replace('"', '')

        if chosen_agent not in ['sales', 'inventory', 'finance']:
            print(f"[MANAGER] Warning: Gemini gave invalid choice '{chosen_agent}'. Defaulting to 'sales'.")
            chosen_agent = 'sales' 
        
        print(f"[MANAGER] Gemini's Decision: Route to --> {chosen_agent.upper()} <---")

    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        def error_stream(error_message): yield f"Error: The Manager Agent (Gemini) failed. {error_message}"
        return StreamingHttpResponse(error_stream(str(e)), status=500, content_type="text/plain")

    # Agent Chaining: We simulate a new request to the specialist agent, passing Gemini's decision.
    # This promotes code re-use and separation of concerns.
    # Agent Chaining: We simulate a new request to the specialist agent, passing Gemini's decision.
    print(f"[MANAGER] Chaining request to '{chosen_agent.upper()}' specialist...")
    
    # Create a new request object to pass to the specialist function
    specialist_request = HttpRequest()
    
    # Set the method
    specialist_request.method = 'POST'
    
    # Set other necessary attributes from the original request
    specialist_request.META = request.META.copy()
    specialist_request.COOKIES = request.COOKIES.copy()
    
    # We set the '_body' private attribute, which is the correct way to assign content
    # to a manually created HttpRequest object.
    specialist_request._body = json.dumps({
        'question': question,
        'history': history,
        'agent': chosen_agent
    }).encode('utf-8')
    
    # The manager's job is done. It now hands off the request to the chosen specialist.
    return specialist_agent_api(specialist_request)