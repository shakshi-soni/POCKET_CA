from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
import src.tools as project_tools

def get_agent_core(llm: ChatGroq):
    # Pack active tools array
    tools_list = [
        project_tools.tax_saving, 
        project_tools.legal_section, 
        project_tools.gst_calculator, 
        project_tools.invoice_generator, 
        project_tools.standard_lookup
    ]
    
    agent_system_prompt = """You are Pocket CA Premium Elite. You have an advanced cognitive brain for parsing informal Indian business requests.

    CRITICAL INSTRUCTIONS FOR REASONING:
    1. Convert text numbers to strict digits: "2.45 lakhs" = 245000, "1 lakh" = 100000, "50k" = 50000.
    2. Clean up spellings: If the user says "lenga", map it to "Lehenga Choli" in the item description.
    3. Strict Tool Argument Rules: The `items` argument for `invoice_generator` MUST be a valid JSON array string containing structured dictionaries. 
       Example format: '[{"name": "Lehenga Choli", "price": 245000, "qty": 1}]'
    4. If fields like invoice_no, client_name, client_phone, client_email, or client_address are missing from the chat conversation, do not fail! Automate them with clean placeholders like "INV-2026-999", "In-Store Guest", "9999999999", "client@internal.me", and "Counter Delivery".

    Execute with extreme professionalism, clean tabular outputs, and complete accuracy."""

    return create_react_agent(llm, tools_list, prompt=agent_system_prompt)
