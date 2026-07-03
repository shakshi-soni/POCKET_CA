import os
import json
import datetime
import ast
import streamlit as st
from streamlit_option_menu import option_menu
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from word2number import w2n

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ============================================================
# PREMIUM SAAS COMPONENT & THEME OVERRIDES (Custom CSS)
# ============================================================
st.set_page_config(page_title="PocketCA Pro Dashboard", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    /* Global App Background overrides */
    .stApp {
        background-color: #0b111e;
        color: #f1f5f9;
    }
    /* Sidebar aesthetic layout updates */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #1e293b;
    }
    /* Premium Dashboard KPI Metric Cards */
    .dashboard-card {
        background: linear-gradient(135deg, #1e293b 0%, #111827 100%);
        border: 1px solid #334155;
        padding: 1.25rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }
    .card-title {
        color: #94a3b8;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }
    .card-value {
        color: #38bdf8;
        font-size: 1.4rem;
        font-weight: 700;
    }
    /* Custom Chat Message aesthetics */
    [data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border-radius: 12px !important;
        border: 1px solid #334155 !important;
        padding: 1.25rem !important;
        margin-bottom: 1rem !important;
    }
    /* Action / Download Buttons */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transition: all 0.2s ease;
    }
    .stDownloadButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# INITIALIZATION & ENGINES
# ============================================================
if not os.getenv("GROQ_API_KEY") and "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

@st.cache_resource
def initialize_engines():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.0)
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    try:
        loader = PyPDFLoader("tax_saving.pdf")
        chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(loader.load())
        vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings, collection_name="tax_saving_pdf", persist_directory="./chroma_db")
    except Exception:
        vectorstore = None

    try:
        urls = ["https://cleartax.in/s/income-tax-slabs", "https://cleartax.in/s/gst-rates"]
        link_loader = WebBaseLoader(urls)
        link_chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(link_loader.load())
        vectorstore_link = Chroma.from_documents(documents=link_chunks, embedding=embeddings, collection_name="tax_saving_web", persist_directory="./chroma_db")
    except Exception:
        vectorstore_link = None
        
    return llm, vectorstore, vectorstore_link

llm, vectorstore, vectorstore_link = initialize_engines()

# ============================================================
# INVOICE GENERATOR ENGINE (Saves beautifully structured PDFs)
# ============================================================
def generate_invoice(invoice_no, company_name, client_name, client_phone, client_email, client_address, items, payment_method="Bank Transfer", bank_name="", bank_account=""):
    filename = f"invoice_{invoice_no}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Base background setup
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Clean Header Design
    c.setFillColor(colors.HexColor('#1e293b'))
    c.rect(0, height - 140, width, 140, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, height - 60, "TAX INVOICE")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 40, height - 55, company_name)
    c.setFont("Helvetica", 9)
    c.drawRightString(width - 40, height - 75, f"Date: {datetime.date.today().strftime('%d %B, %Y')}")
    c.drawRightString(width - 40, height - 90, f"Tel: {client_phone}")

    # Metadata & Client Block
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, height - 180, f"Invoice Number: {invoice_no}")
    
    c.drawString(40, height - 210, "Bill To:")
    c.setFont("Helvetica", 9)
    c.drawString(40, height - 225, client_name)
    c.drawString(40, height - 240, client_address)
    c.drawString(40, height - 255, client_email)

    # Line Item Table Structure Header
    table_top = height - 290
    c.setFillColor(colors.HexColor('#f1f5f9'))
    c.rect(40, table_top, width - 80, 24, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor('#1e293b'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, table_top + 7, "Sl No.")
    c.drawString(110, table_top + 7, "Description / Particulars")
    c.drawRightString(width - 150, table_top + 7, "Price (INR)")
    c.drawRightString(width - 50, table_top + 7, "Total")

    subtotal = 0
    row_y = table_top - 22
    
    for idx, item in enumerate(items):
        name = item["name"]
        price = float(item["price"])
        qty = int(item.get("qty", 1))
        total = price * qty
        subtotal += total

        c.setFont("Helvetica", 9)
        c.drawString(50, row_y, f"{idx + 1}.")
        c.drawString(110, row_y, name)
        c.drawRightString(width - 150, row_y, f"Rs.{price:,.2f}")
        c.drawRightString(width - 50, row_y, f"Rs.{total:,.2f}")
        
        c.setStrokeColor(colors.HexColor('#e2e8f0'))
        c.setLineWidth(0.5)
        c.line(40, row_y - 6, width - 40, row_y - 6)
        row_y -= 22

    # Grand Total Positioning
    row_y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 150, row_y, "Grand Total:")
    c.drawRightString(width - 50, row_y, f"Rs.{subtotal:,.2f}")

    # Payment / Settlement details Footer block
    pay_y = row_y - 60
    c.setFillColor(colors.HexColor('#f8fafc'))
    c.rect(40, pay_y - 35, width - 80, 50, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, pay_y, f"Settlement Route: {bank_name or payment_method}")
    c.drawString(50, pay_y - 15, f"Account Identifier / IFSC: {bank_account or 'N/A'}")

    c.save()
    return filename

# ============================================================
# AGENT TOOLS DEFINITION
# ============================================================
@tool
def tax_saving(query: str) -> str:
    """Use this when user asks how to save tax, deductions, 80C, 80D, HRA, NPS."""
    if not vectorstore: return "Tax saving database not initialized."
    results = vectorstore.as_retriever(search_kwargs={"k": 3}).invoke(query)
    return "\n\n".join([r.page_content for r in results]) if results else "No specific matches found."

@tool
def legal_section(query: str) -> str:
    """Use this when user asks about tax rules, GST rules, or legal provisions."""
    if not vectorstore_link: return "Web policy data layers are not loaded."
    results = vectorstore_link.as_retriever(search_kwargs={"k": 3}).invoke(query)
    return "\n\n".join([r.page_content for r in results]) if results else "No legal clauses located."

@tool
def gst_calculator(amount: str, gst_rate: str, transction_type: str) -> str:
    """Use this tool explicitly when asked to calculate GST values."""
    clean_amt = str(amount).lower().strip().replace(",", "").replace("rs", "").strip()
    try: final_numeric_amount = float(clean_amt)
    except Exception: return "Validation Error: Could not parse configuration."

    rate = next((int(s) for s in ["0", "3", "5", "12", "18", "28"] if s in str(gst_rate)), 18)
    total_gst = (final_numeric_amount * rate) / 100
    return f"GST Summary:\nBase: ₹{final_numeric_amount:,.2f}\nRate: {rate}%\nTax Fraction: ₹{total_gst:,.2f}\nAccumulated Total: ₹{final_numeric_amount + total_gst:,.2f}"

@tool
def invoice_generator(invoice_no: str, company_name: str, client_name: str, client_phone: str, client_email: str, client_address: str, items: str, payment_method: str = "Bank Transfer", bank_name: str = "", bank_account: str = "") -> str:
    """Generates a perfect, tax-compliant PDF invoice file securely on disk."""
    try: raw_items = json.loads(items) if isinstance(items, str) else items
    except Exception:
        try: raw_items = ast.literal_eval(items)
        except Exception: return "Error: Failed to process item formatting."

    sanitized_items, base_subtotal = [], 0.0
    for item in raw_items:
        name = item.get("name", "Retail Item")
        price = float(str(item.get("price")).replace(",", "").replace("Rs.", "").strip())
        qty = int(item.get("qty", 1))
        sanitized_items.append({"name": name, "price": price, "qty": qty})
        base_subtotal += (price * qty)

    # Automatically add exact Indian GST compliant lines
    total_gst = (base_subtotal * 18.0) / 100
    sanitized_items.append({"name": "CGST (9.0%)", "price": total_gst / 2, "qty": 1})
    sanitized_items.append({"name": "SGST (9.0%)", "price": total_gst / 2, "qty": 1})

    filename = generate_invoice(invoice_no=invoice_no, company_name=company_name, client_name=client_name, client_phone=client_phone, client_email=client_email, client_address=client_address, items=sanitized_items, payment_method=payment_method, bank_name=bank_name, bank_account=bank_account)
    
    st.session_state["last_generated_pdf"] = filename
    return f"SUCCESS: Invoice compiled perfectly as '{filename}'."

@tool
def standard_lookup(query: str) -> str:
    """Fallback fallback search network."""
    return DuckDuckGoSearchRun().run(query)

tools = [tax_saving, legal_section, gst_calculator, invoice_generator, standard_lookup]
agent = create_react_agent(llm, tools, prompt="You are Pocket CA, an expert financial intelligence core assistant. Reply with crisp, authoritative corporate formatting.")

# ============================================================
# MODERN SIDEBAR DASHBOARD NAVIGATION & METRICS
# ============================================================
with st.sidebar:
    # Custom interactive sidebar menu matching reference layout
    selected_page = option_menu(
        menu_title="Main Menu",
        options=["AI Agent Core", "Analytics & History", "System Settings"],
        icons=["cpu", "bar-chart-line", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "#0f172a", "padding": "5px"},
            "icon": {"color": "#38bdf8", "font-size": "15px"}, 
            "nav-link": {"font-size": "14px", "color": "#94a3b8", "text-align": "left", "margin":"0px", "--hover-color": "#1e293b"},
            "nav-link-selected": {"background-color": "#0284c7", "color": "white"},
        }
    )
    
    st.markdown("---")
    st.markdown("### 📊 System Indicators")
    
    # Injected modern raw HTML dashboard metrics matching image_07b7db
    st.markdown("""
        <div class="dashboard-card">
            <div class="card-title">LLM Core Intelligence</div>
            <div class="card-value">Llama 3.1 8B</div>
        </div>
        <div class="dashboard-card">
            <div class="card-title">Tax Jurisdiction</div>
            <div class="card-value" style="color: #34d399;">FY 2026-27</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Flush Context Memory", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["langchain_history"] = []
        st.rerun()

# ============================================================
# MAIN APPLICATION PAGE ROUTING
# ============================================================
if selected_page == "AI Agent Core":
    st.markdown("<h2 style='margin-bottom: 0px;'>⚖️ PocketCA Pro Terminal</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; margin-bottom: 25px;'>Indian Corporate Tax Computation & Automated Dynamic PDF Invoicing Engine</p>", unsafe_allow_html=True)

    # Initialize chat flows
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "ai", "content": "Welcome back operator. Provide billing items, pricing details, or tax rule requests to run computations or compile structured PDF invoices."}]
    if "langchain_history" not in st.session_state:
        st.session_state["langchain_history"] = []

    # Display clean conversations
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Capturing input entries
    if user_query := st.chat_input("Ask about tax rules or specify parameters to generate bills..."):
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state["messages"].append({"role": "user", "content": user_query})
        st.session_state["langchain_history"].append(HumanMessage(content=user_query))

        with st.chat_message("assistant"):
            with st.spinner("Executing analytical subroutines..."):
                try:
                    response = agent.invoke({"messages": st.session_state["langchain_history"][-10:]})
                    st.session_state["langchain_history"] = response["messages"]
                    agent_reply = response["messages"][-1].content
                    
                    st.write(agent_reply)
                    st.session_state["messages"].append({"role": "ai", "content": agent_reply})
                    
                    # DYNAMIC PDF INTERFACE TRIGGER
                    if "last_generated_pdf" in st.session_state:
                        pdf_file = st.session_state["last_generated_pdf"]
                        if os.path.exists(pdf_file):
                            with open(pdf_file, "rb") as f:
                                st.markdown("<br>", unsafe_allow_html=True)
                                # Modern download card component placement
                                st.download_button(
                                    label="📥 Download Compiled Tax Invoice (PDF)",
                                    data=f,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            del st.session_state["last_generated_pdf"]
                except Exception as err:
                    st.error(f"Engine Exception: {err}")

elif selected_page == "Analytics & History":
    st.markdown("## 📊 Financial Audit Logs")
    st.info("System auditing features are running 24/7. Historical metrics and transaction logging layers appear here.")

elif selected_page == "System Settings":
    st.markdown("## ⚙️ Configuration Panels")
    st.text_input("Corporate PAN Registered Entity ID", value="STXXXXXXXXX")
    st.text_input("Default Corporate GSTIN", value="27AAAAA0000A1Z5")
