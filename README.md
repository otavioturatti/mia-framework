<p align="center">
  <h1 align="center">MIA</h1>
  <p align="center"><strong>Map of Intent and Action</strong></p>
  <p align="center">A framework for mapping natural language into structured, executable actions.<br/>Built for AI agents that need to understand what users mean — not just what they say.</p>
</p>

<p align="center">
  <a href="#the-problem">The Problem</a> ·
  <a href="#the-solution">The Solution</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#using-mia-as-rag">Using MIA as RAG</a> ·
  <a href="#architecture-patterns">Architecture Patterns</a> ·
  <a href="#production-guide">Production Guide</a> ·
  <a href="#license">License</a>
</p>

---

## The Problem

You're building an AI agent that converts natural language into actions — SQL queries, API calls, tool executions. The user asks:

> *"How much did I sell yesterday?"*

Sounds simple. But:

- **"I"** — is this a salesperson asking about their sales? A manager asking about their store? A director asking about the region?
- **"sell"** — which table? `sales`? `orders`? `transactions`? `receipts`?
- **"yesterday"** — `CURRENT_DATE - 1`? What about timezone?

Now multiply this by hundreds of possible questions, business jargon that no LLM knows, and domain-specific logic that lives only in people's heads.

**This is the gap MIA fills.**

## The Solution

**MIA** (Map of Intent and Action) is a structured framework that decomposes ambiguous natural language into executable actions through four columns:

| Question | Intent | Operation | Action |
|----------|--------|-----------|--------|
| *What the user said* | *What they actually meant* | *How to solve it* | *What to execute* |

Each column progressively removes ambiguity:

```
"How much did I sell yesterday?"
        ↓
"Total store revenue for the previous day"        ← Intent (disambiguated)
        ↓
"Sum of sales values filtered by date = yesterday" ← Operation (logic)
        ↓
SQL: SELECT SUM(amount) FROM sales WHERE date = CURRENT_DATE - 1  ← Action (executable)
```

### MIA captures what schemas can't

Business domains are full of implicit knowledge. In a supermarket, *"How many customers did I have?"* doesn't mean counting rows in a `customers` table — it means counting **receipts issued**. No database schema tells you that. No LLM knows that. But MIA does:

| Question | Intent | Operation | Action |
|----------|--------|-----------|--------|
| How many customers did I have yesterday? | Number of receipts issued yesterday | Count of receipts filtered by date = yesterday | `SELECT COUNT(*) FROM receipts WHERE date = CURRENT_DATE - 1` |

## How It Works

A MIA file is an Excel spreadsheet with two sheets:

### Sheet 1: Identity

Metadata that defines the scope of this MIA.

| Field | Description |
|-------|-------------|
| **Name** | Unique identifier (e.g., "MIA Sales") |
| **Domain** | Business area covered (e.g., "Sales Module") |
| **Data Source** | Where the agent executes actions (e.g., "PostgreSQL sales_db") |
| **Agent** | Which agent consumes this MIA (e.g., "sales-agent-v1") |
| **Version** | Document evolution control |
| **Description** | One-line scope summary |

### Sheet 2: Map

The core table. Four columns, always the same — regardless of whether it's an orchestrator, a specialist agent, or a monolith.

**Examples across different action types:**

| Question | Intent | Operation | Action |
|----------|--------|-----------|--------|
| How much did I sell yesterday? | Total store revenue yesterday | Sum of sales filtered by date | `SQL: SELECT SUM(amount) FROM sales WHERE date = CURRENT_DATE - 1` |
| What's the status of my order? | Track current order status | Lookup order by user ID via logistics API | `API: GET /api/v1/tracking/{order_id}` |
| Let the team know the report is ready | Send notification about report completion | Identify team channel and compose message | `Tool: send_slack_message(channel='#sales', text='Report ready')` |
| I need a report on sales and inventory | Generate cross-domain report | Identify domains: Sales + Inventory | `Route -> Sales Agent + Inventory Agent` |

### Same question, different profiles

When user profiles change behavior, duplicate the row — the Intent naturally differentiates:

| Question | Intent | Operation | Action |
|----------|--------|-----------|--------|
| How much did I sell yesterday? | **Store** revenue yesterday | Sum filtered by store and date | `...WHERE store_id = @store` |
| How much did I sell yesterday? | **Salesperson** revenue yesterday | Sum filtered by salesperson and date | `...WHERE salesperson_id = @user` |

No extra columns. No conditional logic. Clean rows, each self-contained.

## Quick Start

### Prerequisites

- Python 3.10+

### Install

```bash
git clone https://github.com/otavioturatti/mia-framework.git
cd mia-framework
pip install -e .
```

This installs the `mia` package and two CLI commands: `mia-generate` and `mia-export`. For development, use `pip install -e ".[dev]"` to include pytest.

### 1. Generate the template

```bash
mia-generate
```

This creates `MIA_Template.xlsx` — a styled spreadsheet with examples and empty rows ready to fill.

### 2. Fill in your MIA

Open the Excel file and:
1. Fill the **Identity** sheet with your project metadata
2. Fill the **Map** sheet with your question-intent-operation-action rows

### 3. Export to JSON

```bash
mia-export examples/MIA_Template.xlsx
```

This generates a `MIA_Template_export.json` where each row becomes a structured document:

```json
{
  "id": "mia_sales_001",
  "content_for_embedding": "How much did I sell yesterday? — Total store revenue for the previous day",
  "content_for_reranking": "Total store revenue for the previous day — Sum of sales values filtered by date = yesterday",
  "metadata": {
    "question": "How much did I sell yesterday?",
    "intent": "Total store revenue for the previous day",
    "operation": "Sum of sales values filtered by date = yesterday",
    "action": "SQL: SELECT SUM(amount) FROM sales WHERE date = CURRENT_DATE - 1",
    "domain": "Sales",
    "version": "1.0"
  }
}
```

**Two embedding fields by design:**
- `content_for_embedding` — **Question + Intent** for primary vector search (richer semantic surface than question alone)
- `content_for_reranking` — **Intent + Operation** for cross-encoder reranking (captures the "what" and "how")
```

## Using MIA as RAG

MIA is designed to be consumed in three ways:

### 1. Design document
Fill the MIA **before** building the agent. It forces you to think through every intent, every edge case, every piece of business jargon.

### 2. Few-shot examples
Feed MIA rows directly into the agent's prompt as examples of how to map questions to actions.

### 3. RAG knowledge base
Embed the MIA and let the agent **search for similar questions at runtime**:

```
User asks: "What were my sales last week?"
       ↓
Semantic search on MIA embeddings
       ↓
Closest match: "How much did I sell yesterday?"
       ↓
Agent reads: Intent + Operation + Action
       ↓
Adapts the pattern to generate the correct response
```

The `content_for_embedding` field contains the **Question + Intent** — this is what gets vectorized. Including Intent means that duplicate questions with different profiles (e.g., "store revenue" vs. "salesperson revenue") produce **different vectors**. The rest comes back as **metadata** after retrieval.

### Why this works

You don't need to list every possible phrasing. RAG works by **semantic similarity**, not exact matching:

- "how much did I sell yesterday" 
- "what was yesterday's revenue"
- "yesterdays sales total"
- "hwat did i sel yestrday" *(typos included)*

All of these land close to the same embedding vector. **One representative question per intent is enough.**

## Architecture Patterns

### Monolith — Single MIA

One agent, one database, one MIA. Simple.

```
User Question → MIA (RAG) → Agent → Database
```

### Microservices — One MIA per domain

Each service has its own agent, its own data, and its own MIA. The MIA defines the "world" each agent can see.

```
User Question → Orchestrator MIA → Routes to domain
                                        ↓
                            ┌───────────────────────┐
                            │  Sales MIA → Sales DB │
                            │  Stock MIA → Stock DB │
                            │  HR MIA → HR System   │
                            └───────────────────────┘
```

The orchestrator itself uses a MIA — its Actions are **routing decisions**, not SQL or API calls.

### The framework is role-agnostic

The four columns stay the same whether you're building an orchestrator or a specialist. What changes is what you write in the **Action** column:

| Role | Action column contains |
|------|----------------------|
| Specialist agent | SQL queries, API calls, tool executions |
| Orchestrator | Routing decisions (`Route -> Agent X`) |

Same framework. Same table. The intelligence is in how you fill it — not in the structure.

## Tips for filling a great MIA

- **One representative question per intent.** Don't list variations — RAG handles semantic similarity.
- **Capture business jargon in the Intent column.** This is where "customers" becomes "receipts issued" and "revenue" becomes `SUM(amount) FROM sales`.
- **Duplicate rows only when profiles change behavior.** If the question "How much did I sell?" means different things to a manager vs. a salesperson, create two rows.
- **The person filling the MIA should know the business.** This isn't a dev task — it's a domain expert task (or both working together).
- **Start small, grow organically.** Begin with the 20 most common questions. The MIA grows as the agent encounters new patterns.

## Production Guide

MIA is a **knowledge authoring framework** — it structures and exports your domain knowledge. The embedding, indexing, retrieval, and generation steps are the responsibility of your pipeline. This section covers how to integrate MIA exports into a production RAG system.

### Retrieval strategy

Use **hybrid search** (vector + keyword) for best results. Pure vector search can miss domain-specific jargon, acronyms, and technical terms that keyword matching handles well.

```
User query
    ↓
┌──────────────────────────┐
│  Vector search (top 20)  │ ← uses content_for_embedding
│  + BM25 keyword (top 20) │ ← uses metadata.question
└──────────────────────────┘
    ↓  merge + deduplicate
┌──────────────────────────┐
│  Cross-encoder reranker  │ ← uses content_for_reranking
└──────────────────────────┘
    ↓  top 3-5
Agent receives context
```

### Metadata filtering

When the same question maps to different actions per user profile, **filter by metadata at query time** — don't rely on embedding distance alone:

```python
results = vector_store.search(
    query_vector=embed(user_query),
    filters={"domain": "sales", "agent": "sales-agent-v1"},
    limit=10,
)
```

The `metadata.domain`, `metadata.agent`, and `metadata.data_source` fields exist for this purpose.

### Confidence threshold and fallback

Not every user question will have a match in the MIA. Define a **minimum similarity threshold** and a fallback strategy:

```python
SIMILARITY_THRESHOLD = 0.75  # tune for your domain

results = search(user_query)
if not results or results[0].score < SIMILARITY_THRESHOLD:
    return "I'm not sure I understand. Could you rephrase your question?"
```

In production, ~30-40% of queries may not have a direct match. Plan for it.

> **Note:** Similarity thresholds vary drastically between embedding models. A score of 0.75 with `text-embedding-3-large` means something completely different than 0.75 with `BGE-M3`. Always calibrate your threshold against a test set of known question-intent pairs from your specific MIA and model combination.

### Action safety

The `action` field in MIA contains **templates, not executable code**. Never interpolate user input directly into action strings. Always:

- Use **parameterized queries** for SQL (`WHERE id = $1`, not string formatting)
- **Validate and sanitize** any dynamic values before execution
- Enforce **role-based access control** at the execution layer — the MIA defines *what* actions exist, not *who* can run them

### Feedback loop

A MIA is a living document that improves over time. Track these metrics:

- **Unmatched queries** — questions with no results above threshold (candidates for new MIA rows)
- **Retrieval quality** — Recall@K, MRR on a test set of known question-intent pairs
- **Action success rate** — did the generated action actually work?

Periodically review unmatched queries and add new rows to the MIA. The more rows, the smarter the agent.

### Scaling beyond Excel

Excel works well up to ~500 rows. Beyond that, consider:

- **CSV/TSV** as primary format, imported into the Excel template for review
- **Database-backed MIA** with an export step to JSON
- **Multiple MIA files** split by domain (the microservices pattern)

The `export.py` module works with any `.xlsx` that follows the MIA structure, regardless of how it was created.

## Project Structure

```
mia-framework/
├── README.md                ← You are here
├── LICENSE                  ← MIT License
├── pyproject.toml           ← Dependencies, metadata, CLI entry points
├── src/mia/                 ← Installable Python package
│   ├── __init__.py
│   ├── exceptions.py        ← Custom MiaError exception
│   ├── generate_template.py ← Generates the Excel template (mia-generate)
│   └── export.py            ← Exports Excel → structured JSON (mia-export)
├── tests/                   ← Unit tests (pytest)
│   ├── test_generate_template.py
│   └── test_export.py
├── .github/workflows/
│   └── ci.yml               ← GitHub Actions CI
└── examples/
    └── MIA_Template.xlsx    ← Ready-to-use template with examples
```

## License

MIT License — do whatever you want with it, just keep the attribution.

---

<p align="center">
  Created with love by <a href="https://www.linkedin.com/in/otavioturatti/">Joao Otavio Turatti Barbosa</a>
</p>
