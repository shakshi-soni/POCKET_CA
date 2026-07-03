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
# 🌌 DEEP SPACE CYBERPUNK SAAS DESIGN SYSTEM (ULTRA PREMIUM)
# ============================================================
st.set_page_config(
    page_title="PocketCA Pro • Premium", 
    page_icon="👑", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Global Application Canvas */
    .stApp {
        background: radial-gradient(circle at 80% 20%, #111c33 0%, #060b14 60%, #03070c 100%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Hide native header decoration line */
    [data-testid="stHeader"] {
        background: rgba(0,0,0,0) !important;
    }

    /* Scrollbars */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #03070c; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 99px; }

    /* Glassmorphic Side Management Console */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 17, 31, 0.95) 0%, rgba(4, 8, 15, 0.98) 100%) !important;
        border-right: 1px solid rgba(56, 189, 248, 0.1) !important;
        backdrop-filter: blur(20px);
    }

    /* Premium Dashboard KPI Matrix Cards */
    .kpi-row {
        display: flex;
        gap: 1.25rem;
        margin-bottom: 2rem;
        flex-wrap: wrap;
    }
    .kpi-glow-card {
        flex: 1;
        min-width: 240px;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.3) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .kpi-glow-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    }
    .kpi-glow-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.25);
        box-shadow: 0 25px 50px -12px rgba(56, 189, 248, 0.15);
    }
    .kpi-label {
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    .kpi-number {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #ffffff, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Terminal Prompt Chat Shells */
    [data-testid="stChatMessage"] {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.4) 0%, rgba(30, 41, 59, 0.2) 100%) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        padding: 1.75rem !important;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem !important;
        transition: border-color 0.2s ease;
    }
    [data-testid="stChatMessage"]:hover {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.12) 0%, rgba(3, 105, 161, 0.05) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
    }

    /* Cybernetic Glowing Action Buttons */
    .stDownloadButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #3b82f6 50%, #6366f1 100%) !important;
        background-size: 200% auto !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em;
        padding: 1rem 2.5rem !important;
        box-shadow: 0 12px 24px -6px rgba(59, 130, 246, 0.4);
        transition: all 0.4s ease !important;
        width: 100%;
    }
    .stDownloadButton>button:hover {
        background-position: right center !important;
        transform: translateY(-2px);
        box-shadow: 0 20px 35px -4px rgba(99, 102, 241, 0.6);
    }
    
    /* Clean Sidebar Flush Layout */
    .flush-btn button {
        background-color: rgba(244, 63, 94, 0.1) !important;
        color: #f43f5e !important;
        border: 1px solid rgba(244, 63, 94, 0.2) !important;
        border-radius: 10px;
    }
    .flush-btn button:hover {
        background-color: #f43f5e !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# INITIALIZATION & MACHINE LAYERS
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
# REPORTLAB HIGH-END MINIMALIST PDF GENERATOR 
# ============================================================
def generate_invoice(invoice_no, company_name, client_name, client_phone, client_email, client_address, items, payment_method="Bank Transfer", bank_name="", bank_account=""):
    filename = f"invoice_{invoice_no}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Crisp minimalist layout mapping
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Premium Corporate Side Strip Design
    c.setFillColor(colors.HexColor('#0f172a'))
    c.rect(0, 0, 30, height, fill=1, stroke=0)
    
    # Header Info Setup
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont("Helvetica-Bold", 28)
    c.drawString(60, height - 70, "INVOICE")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - 50, height - 55, company_name)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#64748b'))
    c.drawRightString(width - 50, height - 72, f"Date Issued: {datetime.date.today().strftime('%d %B, %Y')}")
    c.drawRightString(width - 50, height - 86, f"Contact: {client_phone}")

    # Separator Line
    c.setStrokeColor(colors.HexColor('#cbd5e1'))
    c.setLineWidth(1)
    c.line(60, height - 110, width - 50, height - 110)

    # Client / Meta Split Block
    c.setFillColor(colors.HexColor('#0f172a'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, height - 145, "BILL TO:")
    c.setFont("Helvetica", 10)
    c.drawString(60, height - 162, client_name)
    c.drawString(60, height - 177, client_address)
    c.drawString(60, height - 192, client_email)
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, height - 145, f"Invoice Ref: {invoice_no}")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#64748b'))
    c.drawRightString(width - 50, height - 162, "Status: Regulated Invoice Generated")

    # Table Architecture Definition
    table_top = height - 240
    c.setFillColor(colors.HexColor('#0f172a'))
    c.rect(60, table_top, width - 110, 24, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(75, table_top + 7, "ID")
    c.drawString(130, table_top + 7, "Product/Particular Description")
    c.drawRightString(width - 160, table_top + 7, "Rate")
    c.drawRightString(width - 65, table_top + 7, "Amount")

    subtotal = 0
    row_y = table_top - 22
    
    for idx, item in enumerate(items):
        name = item["name"]
        price = float(item["price"])
        qty = int(item.get("qty", 1))
        total = price * qty
        if "GST" not in name:
            subtotal += total

        c.setFillColor(colors.HexColor('#334155'))
        c.setFont("Helvetica", 9.5)
        c.drawString(75, row_y, f"{idx + 1:02d}")
        c.drawString(130, row_y, name)
        c.drawRightString(width - 160, row_y, f"Rs.{price:,.2f}")
        c.drawRightString(width - 65, row_y, f"Rs.{total:,.2f}")
        
        c.setStrokeColor(colors.HexColor('#f1f5f9'))
        c.setLineWidth(0.5)
        c.line(60, row_y - 6, width - 50, row_y - 6)
        row_y -= 22

    # Math Computation Positioning
    row_y -= 15
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor('#0f172a'))
    c.drawRightString(width - 160, row_y, "Total Aggregate:")
    
    final_aggregate = sum(f["price"] * f["qty"] for f in items)
    c.drawRightString(width - 65, row_y, f"Rs.{final_aggregate:,.2f}")

    # Premium Footer Block
    pay_y = row_y - 70
    c.setFillColor(colors.HexColor('#f8fafc'))
    c.rect(60, pay_y - 35, width - 110, 50, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor('#1e293b'))
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(75, pay_y, f"Settlement Channel: {bank_name or payment_method}")
    c.drawString(75, pay_y - 15, f"Account Routing ID: {bank_account or 'N/A'}")

    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(60, 45, "AUTHORIZED COMPLIANT CORE SIGNATURE GENERATED ELECTRONICALLY.")

    c.save()
    return filename

# ============================================================
# AGENT TOOL SETS
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
agent = create_react_agent(llm, tools, prompt="You are Pocket CA Premium Elite. Use extreme professionalism, bold metric lists, and strict corporate formatting.")

# ============================================================
# 🗺️ PREMIUM NAVIGATION CONTROL CORE
# ============================================================
with st.sidebar:
    st.markdown("<div style='padding:15px 0px;'><h2 style='color:#ffffff; font-weight:900; font-size:1.6rem; letter-spacing:-0.04em;'>👑 POCKETCA<span style='color:#38bdf8;'>.PRO</span></h2></div>", unsafe_allow_html=True)
    
    selected_page = option_menu(
        menu_title=None,
        options=["Operations Hub", "Telemetry Analytics", "Global Ledger Configurations"],
        icons=["sliders2", "cpu-fill", "database-fill-gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"background-color": "transparent", "padding": "0px"},
            "icon": {"color": "#38bdf8", "font-size": "13px"}, 
            "nav-link": {"font-size": "13px", "color": "#94a3b8", "text-align": "left", "padding": "12px 15px", "margin":"5px 0px", "border-radius":"12px", "font-weight": "500"},
            "nav-link-selected": {"background": "linear-gradient(90deg, #0284c7 0%, #2563eb 100%)", "color": "white", "font-weight": "700"},
        }
    )
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:0.7rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:10px; padding-left:5px;'>SYSTEM ARCHITECTURE</p>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:15px; border-radius:14px; margin-bottom:12px;">
            <div style="color:#64748b; font-size:10px; font-weight:700; text-transform:uppercase;">Model Infrastructure</div>
            <div style="color:#ffffff; font-size:14px; font-weight:700; margin-top:2px;">ChatGroq Llama-3.1</div>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:15px; border-radius:14px; margin-bottom:12px;">
            <div style="color:#64748b; font-size:10px; font-weight:700; text-transform:uppercase;">Vector Index Status</div>
            <div style="color:{'#34d399' if vectorstore else '#f43f5e'}; font-size:14px; font-weight:700; margin-top:2px;">
                {'ChromaDB Core Loaded' if vectorstore else 'ChromaDB Local Offline'}
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); padding:15px; border-radius:14px; margin-bottom:20px;">
            <div style="color:#64748b; font-size:10px; font-weight:700; text-transform:uppercase;">Active Web Crawler</div>
            <div style="color:{'#34d399' if vectorstore_link else '#f43f5e'}; font-size:14px; font-weight:700; margin-top:2px;">
                {'ClearTax Live Sync' if vectorstore_link else 'Web Loader Standby'}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='flush-btn'>", unsafe_allow_html=True)
    if st.button("Purge Runtime Context", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["langchain_history"] = []
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# ROUTER DISPLAY PAGE
# ============================================================
if selected_page == "Operations Hub":
    
    st.markdown("<h1 style='font-size:2.75rem; font-weight:900; letter-spacing:-0.04em; margin-bottom:5px; background:linear-gradient(90deg, #ffffff 0%, #38bdf8 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>Cognitive Operations Terminal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:1rem; margin-bottom:35px;'>Deterministic Financial Engineering, Local Vector RAG (ChromaDB), and Dynamically Injected GST/Tax Compiling Pipeline</p>", unsafe_allow_html=True)
    
    # Ultra Pro Max KPI Rows
    st.markdown("""
        <div class="kpi-row">
            <div class="kpi-glow-card">
                <div class="kpi-label">Neural Embedding Sub-Cluster</div>
                <div class="kpi-number" style="color:#38bdf8;">HuggingFace: all-MiniLM-L6-v2</div>
            </div>
            <div class="kpi-glow-card">
                <div class="kpi-label">Isolated Vector Context Partition</div>
                <div class="kpi-number" style="color:#c084fc;">ChromaDB Persistent Store</div>
            </div>
            <div class="kpi-glow-card">
                <div class="kpi-label">Deterministic Compilation Layer</div>
                <div class="kpi-number" style="color:#fde047;">ReportLab Canvas Engine</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "ai", "content": "Operations Hub established. Ready to accept structural variable commands, raw business logs, or invoice matrix parameters."}]
if "langchain_history" not in st.session_state:
        st.session_state["langchain_history"] = []

    # Print streams
for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Processing Input
if user_query := st.chat_input("Dispatch command parameters to agent..."):
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state["messages"].append({"role": "user", "content": user_query})
        st.session_state["langchain_history"].append(HumanMessage(content=user_query))

        with st.chat_message("assistant"):
            with st.spinner("Processing optimization pipelines..."):
                try:
                    response = agent.invoke({"messages": st.session_state["langchain_history"][-10:]})
                    st.session_state["langchain_history"] = response["messages"]
                    agent_reply = response["messages"][-1].content
                    
                    st.write(agent_reply)
                    st.session_state["messages"].append({"role": "ai", "content": agent_reply})
                    
                    # FLOATING BUTTON SHEET GENERATION
                    if "last_generated_pdf" in st.session_state:
                        pdf_file = st.session_state["last_generated_pdf"]
                        if os.path.exists(pdf_file):
                            with open(pdf_file, "rb") as f:
                                st.markdown("<div style='margin-top:20px; padding:4px; border-radius:12px;'>", unsafe_allow_html=True)
                                st.download_button(
                                    label="⚡ EXPORT DETERMINISTIC ENTERPRISE PDF ASSET",
                                    data=f,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                                st.markdown("</div>", unsafe_allow_html=True)
                            del st.session_state["last_generated_pdf"]
                except Exception as err:
                    st.error(f"Runtime Warning: {err}")

elif selected_page == "Telemetry Analytics":
    st.markdown("## 📊 Telemetry Clusters")
    st.info("Performance loops, inference cost metrics, and embedding cluster indexes will monitor here.")

elif selected_page == "Global Ledger Configurations":
    st.markdown("## ⚙         Global Ledger Settings")
    st.text_input("Entity Identification Token (PAN)", value="STXXXXXXXXX")
    st.text_input("Default Institutional Code (GSTIN)", value="27AAAAA0000A1Z5")
