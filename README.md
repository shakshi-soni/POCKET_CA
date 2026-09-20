

# PocketCA Pro

A conversational bookkeeping assistant for Indian small businesses. You describe a sale in plain language — including regional shorthand like "lakhs" or "k" — and it turns that into a GST-correct invoice, split into CGST/SGST, as a downloadable PDF.

Not a filing tool. It calculates and generates documents, it doesn't submit anything to a government portal.

> "Sold 3 units of rice at 2.5k each, 5% GST" → extracted into quantity/rate/tax slab → calculator computes the GST split → PDF invoice generated.

[![Live Demo](https://img.shields.io/badge/🚀-Live_Demo-2ea44f?style=for-the-badge)](https://pocketca-f6bt3bbtuf9mhxchtsg8bb.streamlit.app/)


## What it does

The core decision I made early on: the LLM never touches the math. It parses intent and extracts numbers — item, quantity, rate, tax slab — and a deterministic Python calculator does the actual tax computation. That split exists specifically because LLMs are unreliable at arithmetic, and a wrong tax number on an invoice isn't a minor bug.

Beyond invoicing, there's a RAG layer for general GST policy questions (separate from the calculator — it doesn't feed into invoice numbers), with a DuckDuckGo fallback when the local documents don't have an answer.

## Architecture

```
Streamlit frontend
        ↓
LangGraph ReAct agent (Groq — Llama 3.1 8B)
        ↓
   ┌────┴────┬──────────────┐
   ↓         ↓              ↓
GST         Chroma RAG    PDF generator
calculator  (policy Q&A)  (ReportLab)
(no LLM,
deterministic)
```

The agent reads the conversation, decides if a tool call is needed, calls it, reads the result, replies. The calculator and PDF generator are tightly coupled — the calculator's output is what actually gets printed on the invoice, so the number the agent says in chat and the number on the PDF invoice come from the same computation, not two separate guesses. The RAG path is separate and only used for policy questions, it doesn't touch invoice numbers.

## How the GST calculator works

- Cleans monetary input — strips commas, currency symbols, "lakhs"/"k" shorthand
- Matches the transaction to one of the five GST slabs: 0/5/12/18/28%
- Computes the taxable base and GST amount
- Splits GST into CGST + SGST — assumes intra-state by default, doesn't currently handle IGST for inter-state sales
- Returns a structured result consumed directly by the PDF generator

Worth being explicit: this app doesn't file returns, respond to GST notices, or talk to the government portal. If a business gets a mismatch notice or a late-filing issue, that still needs a CA to handle through the actual portal. This just keeps records clean enough that the process is easier.

## Running locally

```bash
git clone https://github.com/shakshi-soni/POCKET_CA_PRO.git
cd POCKET_CA_PRO
pip install -r requirements.txt
export GROQ_API_KEY="your-key-here"
streamlit run app.py
```

## Tech stack

Streamlit for the UI, LangGraph for the ReAct agent loop, Groq running Llama 3.1 8B, ChromaDB + `all-MiniLM-L6-v2` embeddings for retrieval, `RecursiveCharacterTextSplitter` for chunking, ReportLab for the actual PDF rendering (vector, not an HTML-to-PDF conversion), DuckDuckGo as a fallback search when local docs miss.

## Project structure

```
POCKET_CA_PRO/
├── assets/
│   └── architecture_diag.png
├── config/
│   └── ledger_settings.json
├── data/
│   └── tax_saving.pdf
├── src/
│   ├── agent.py
│   ├── tools.py
│   ├── utils.py
│   └── __init__.py
├── workflows/
├── app.py
├── requirements.txt
└── README.md
```

## Limitations

This is a learning project, not a production system.

- No persistent database — transactions live in `st.session_state`, gone when the browser session ends
- Runs on Groq's free tier and Streamlit Community Cloud — both rate-limited, idles out after inactivity
- Regional-term parsing ("lakhs", "k") is handled through prompt instructions to the LLM, not a dedicated NLP pipeline — accuracy depends on how close the input is to what I tested
- RAG retrieval is a separate path from the calculator, it doesn't cross-check slab numbers against source documents
- No auth, no multi-user support, no invoice history across sessions
- CGST/SGST only — no IGST for inter-state transactions yet
- PDF output isn't encrypted or access-controlled, it's just a clean vector render

## What I'd improve next

1. Wire RAG retrieval into the calculator so slab decisions can be checked against source documents
2. Persistent invoice history instead of session-only state
3. A tested phrase bank for regional terms instead of relying on prompt instructions
4. Automated tests for the GST calculator's edge cases
5. IGST support for inter-state transactions
6. CSV/Excel export for handoff to an actual accountant

## Why I built this

GST invoicing for small businesses in India is still mostly manual — spreadsheets, calculators, someone doing CGST/SGST math by hand. I wanted to see if a conversational interface could actually remove that friction without introducing a worse problem, which is why the LLM-does-language / code-does-math split was the first decision I made, not an afterthought. Everything else in the project — the RAG layer, the PDF generation, the regional-term handling — was really in service of that one constraint: never let the model touch the tax number that ends up on a real invoice.

## About

Shakshi Soni.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/shakshi-soni-961048411/)
