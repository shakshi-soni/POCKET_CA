🧾 PocketCA Pro
================

**Talk to your books. Get GST-correct invoices back — no spreadsheets, no manual tax math.**

[![Live Demo](https://img.shields.io/badge/🚀-Live_Demo-2ea44f?style=for-the-badge)](https://pocketca-f6bt3bbtuf9mhxchtsg8bb.streamlit.app/)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-6E56CF?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-Llama_3.1-F55036?style=for-the-badge)

---

## 🔵 What Is This?

PocketCA Pro is a conversational bookkeeping assistant for Indian small businesses. Tell it about a sale in plain language — including regional shorthand like *"lakhs," "k,"* or informal product names — and it turns that into a structured invoice with GST computed and split into CGST/SGST, ready to download as a PDF.

The core design choice: **the LLM never touches the math.** It parses your intent and extracts the numbers; a deterministic Python calculator does the actual tax computation. That split exists specifically to avoid the classic problem of language models confidently getting arithmetic wrong.

> ⚠️ **Note:** This is a bookkeeping and invoicing tool, not a filing or e-way bill system. It calculates and generates documents — it doesn't submit anything to government portals.

**Example:**
> *"Sold 3 units of rice at 2.5k each, 5% GST"*
→ agent extracts quantity, rate, tax slab → calculator computes base cost + GST split → PDF invoice generated → download button lights up in the sidebar.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 💬 **Conversational Entity Parsing** | Understands casual, regional business phrasing and converts it into structured transaction data |
| 🔢 **Deterministic GST Calculator** | Tax math is handled by code, not the LLM — computes 0/5/12/18/28% slabs and CGST/SGST splits exactly |
| 📚 **Policy Lookup (RAG)** | Semantic search over local tax documents using ChromaDB + HuggingFace embeddings, for general policy Q&A |
| 🌐 **Web Fallback Search** | DuckDuckGo search kicks in when local documents don't have an answer |
| 🖨️ **Instant PDF Invoices** | Renders a clean vector invoice straight to A4 using ReportLab — no HTML-to-PDF conversion step |
| 🎨 **Custom Dashboard UI** | Dark-themed Streamlit interface with sidebar navigation via `streamlit_option_menu` |
| 🧮 **CGST/SGST Auto-Split** | Every taxable transaction is automatically broken into CGST + SGST halves, matching how Indian intra-state GST invoices are structured |
| 🗂️ **Configurable Business Profile** | Business name, GSTIN, and address are pulled from `config/ledger_settings.json`, so invoices are branded without touching code |
| 🔄 **Live Session Recovery** | On invoice creation, the app auto-detects the newest generated PDF and surfaces it without a manual refresh |

---

## 🧠 How It Works — Step by Step

### 1. Saving a transaction
When you describe a sale or purchase, the agent extracts structured fields (item, quantity, rate, tax slab) and passes them to the GST calculator tool. The computed result — base amount, CGST, SGST, total — is what actually gets used to generate the invoice. There's currently no persistent database; each transaction lives in `st.session_state` for the length of the browser session, and ledger defaults (business name, GSTIN, address) are read from `config/ledger_settings.json`.

> If you need transactions to persist across sessions (so you can look up last week's invoice later), that's not built yet — see Roadmap below.

### 2. Generating an invoice
Once a transaction is confirmed, `tools.py` computes the tax split and hands the final numbers to the ReportLab compiler, which paints a vector invoice (line items, CGST/SGST breakdown, totals, date) directly onto an A4 canvas and saves it to disk with a timestamped filename. The app then finds that file via `glob`, stores its path in session state, and surfaces a download button in the sidebar.

### 3. GST Calculator — what it actually does
- Cleans and normalizes monetary input (strips commas, currency symbols, "lakhs"/"k" shorthand)
- Matches the transaction to one of the five standard GST slabs: 0%, 5%, 12%, 18%, 28%
- Computes the taxable base value and the GST amount on it
- Splits GST equally into CGST + SGST (assumes an intra-state transaction by default — it does not currently distinguish IGST for inter-state sales)
- Returns a structured result that the PDF generator consumes directly, so the number the agent states in chat and the number printed on the invoice come from the same calculation, not two separate guesses

### 4. GST notices & penalties — what this app does *not* do
Worth being explicit here, since it's a common point of confusion: PocketCA Pro **calculates and documents** — it does not file returns, respond to notices, or interact with the GST portal. If a real business receives a GST notice (e.g. a mismatch between GSTR-1 and GSTR-3B, late filing, or an input tax credit discrepancy), that requires a human — typically a CA — to respond through the government portal within the notice's deadline. This tool can help keep clean, well-documented records that make that process easier, but it has no notice-handling or compliance-filing functionality, and makes no claim about protecting anyone from penalties.

---

## 🏗️ Architecture

![Architecture Diagram](assets/architecture_diag.png)

```
┌───────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                        │
│              (custom CSS, sidebar, chat interface)            │
└───────────────────────────┬───────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────┐
│                  LangGraph ReAct Agent                        │
│                 (Groq — Llama 3.1 8B)                         │
│                                                               │
│   Reads conversation state → decides if a tool call is        │
│   needed → invokes tool → reads tool output → responds        │
└──────┬──────────────────┬──────────────────┬──────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌──────────────┐  ┌───────────────────┐  ┌─────────────────┐
│ 🔢 GST       │  │ 📚 Chroma RAG    │  │🖨️PDF Generator  │
│ Calculator   │  │ (policy lookup)   │  │ (ReportLab)     │
│ (tools.py)   │  │                   │  │                 │
│              │  │ tax_saving.pdf    │  │ Renders invoice │
│ Deterministic│  │ → chunked →       │  │ to A4 canvas,   │
│ tax-bracket  │  │ HuggingFace       │  │ saves to disk,  │
│ math, no LLM │  │ embeddings        │  │ session_state   │
│ involved     │  │ (all-MiniLM-L6-v2)│  │ picks up latest │
│              │  │ → ChromaDB        │  │ file via glob   │
└──────────────┘  └───────────────────┘  └─────────────────┘
```

**How the pieces connect:**
- The GST calculator and the invoice output are tightly coupled — calculator results drive the numbers on the PDF directly.
- The Chroma RAG layer is a **separate path** used for answering general tax/policy questions. It does not feed into or override the calculator.
- When a tool call confirms an invoice was generated, the app scans the working directory for the latest timestamped PDF, stores its path in `st.session_state`, and calls `st.rerun()` to surface a download button in the sidebar.

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| UI | Streamlit + `streamlit_option_menu` | Chat interface, dark-theme CSS, sidebar navigation |
| Agent orchestration | LangGraph | Cyclical ReAct loop (reason → act → observe) |
| LLM | Groq API — Llama 3.1 8B | Entity parsing and conversational responses |
| Retrieval | ChromaDB + HuggingFace `all-MiniLM-L6-v2` (384-dim) | Semantic search over local tax policy PDFs |
| Document loading | `PyPDFLoader`, `WebBaseLoader` | Ingests local PDFs and web-sourced policy pages |
| Chunking | `RecursiveCharacterTextSplitter` | Splits documents for embedding |
| Tax computation | Custom Python (`tools.py`) | Deterministic GST slab logic, CGST/SGST split |
| PDF generation | ReportLab (`Canvas`) | Vector invoice rendering, no HTML conversion |
| Fallback search | DuckDuckGo Search | Backup lookup when local retrieval misses |

---

## 📂 Project Structure

```
POCKET_CA_PRO/
├── assets/
│   └── architecture_diag.png
├── config/
│   └── ledger_settings.json      # tax slab config, invoice formatting defaults
├── data/
│   └── tax_saving.pdf            # source document for RAG ingestion
├── src/
│   ├── agent.py                  # LangGraph ReAct agent definition
│   ├── tools.py                  # GST calculator + tool-decorated functions
│   ├── utils.py                  # helper functions (parsing, formatting)
│   └── __init__.py
├── workflows/                    # LangGraph graph/state definitions
├── app.py                        # Streamlit entrypoint
├── requirements.txt
└── README.md
```

---

## ⚡ Running Locally

```bash
git clone https://github.com/shakshi-soni/POCKET_CA_PRO.git
cd POCKET_CA_PRO
pip install -r requirements.txt
```

Set your Groq API key:

```bash
export GROQ_API_KEY="your-key-here"
```

Run the app:

```bash
streamlit run app.py
```
---

## ⚠️ Known Limitations

Being upfront about scope, since this is a learning project rather than a production system:

- **Free-tier dependencies** — runs on Groq's free API tier and Streamlit Community Cloud, both rate-limited and prone to idling out after inactivity.
- **RAG scope** — the Chroma retrieval layer answers general policy questions; it isn't wired into the calculator's decision logic.
- **Entity parsing coverage** — regional-term normalization is handled through prompt instructions to the LLM, not a dedicated NLP pipeline, so accuracy depends on how close an input is to tested patterns.
- **No auth or multi-user support** — session state is local to a single browser session; no persistent accounts or invoice history yet.
- **PDF output is not encrypted** — "secure" here means clean vector rendering, not password protection or access control.

---

## 🗺️ Roadmap

- [ ] Wire RAG retrieval into calculator context for slab verification against source documents
- [ ] Add persistent invoice history (currently session-only)
- [ ] Expand regional term normalization with a tested phrase bank
- [ ] Add automated tests for GST calculator edge cases
- [ ] Support IGST calculation for inter-state transactions (currently CGST/SGST intra-state only)
- [ ] Add a basic notices/deadline tracker (informational only — not a filing tool)
- [ ] Export ledger history as CSV/Excel for handoff to an accountant

---

## 🙋‍♂️ About the Developer

Built with ❤️ by **[SHAKSHI SONI]**

I'm a developer passionate about building practical AI applications that solve real-world problems. This project explores agentic AI design — where an LLM doesn't just chat, but *acts*, by calling tools, remembering context, and making decisions autonomously.
---

📫 **Connect with me:**
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/yourprofile)


<div align="center">

**⭐ If you found this project interesting, please give it a star! It helps a lot.**
