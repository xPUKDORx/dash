# CLAUDE.md

This file provides context for Claude Code when working with this repository.

## Project Overview

Data Agent - A self-learning data agent that provides **insights**, not just query results. Inspired by [OpenAI's internal data agent](https://openai.com/index/how-openai-built-its-data-agent/).

Implements 6 layers of context for grounded SQL generation using the Agno framework.

## Architecture

```
data-agent/
├── app/main.py                  # AgentOS entry point
├── da/                          # The Data Agent
│   ├── agent.py                 # Main agent with all 6 layers
│   ├── context/                 # Context builders (Layers 1-3)
│   │   ├── semantic_model.py    # Layer 1: Table metadata
│   │   ├── business_rules.py    # Layer 2: Business rules
│   │   └── query_patterns.py    # Layer 3: Query patterns
│   ├── tools/                   # Agent tools
│   │   ├── analyze.py           # Result analysis
│   │   ├── introspect.py        # Layer 6: Runtime schema
│   │   └── save_query.py        # Save validated queries
│   ├── scripts/                 # Utility scripts
│   │   └── load_data.py         # Load F1 sample data
│   └── evals/                   # Evaluation suite
├── knowledge/                   # Static knowledge files
│   ├── tables/                  # Table metadata (JSON)
│   ├── business/                # Business rules (JSON)
│   └── queries/                 # Validated SQL patterns
└── db/                          # Database utilities
    ├── url.py                   # Database URL builder
    └── session.py               # PostgresDb helper
```

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | AgentOS entry point, registers data agent |
| `da/agent.py` | Main agent with 6 layers, LearningMachine, gpt-5.2 |
| `da/context/*.py` | Context builders for Layers 1-3 |
| `da/tools/*.py` | Agent tools (analyze, introspect, save_query) |
| `db/session.py` | `get_postgres_db()` helper for database connections |
| `db/url.py` | Builds database URL from environment |
| `knowledge/tables/*.json` | Table metadata with data quality notes |
| `knowledge/business/*.json` | Metrics, rules, common gotchas |
| `compose.yaml` | Local development with Docker |
| `railway.json` | Railway deployment config |

## Development Setup

### Virtual Environment

Use the venv setup script to create the development environment:

```bash
./scripts/venv_setup.sh
source .venv/bin/activate
```

### Format & Validation

Always run format and lint checks using the venv Python interpreter:

```bash
source .venv/bin/activate && ./scripts/format.sh
source .venv/bin/activate && ./scripts/validate.sh
```

## Commands

```bash
# Setup virtual environment
./scripts/venv_setup.sh
source .venv/bin/activate

# Local development with Docker
docker compose up -d --build

# Load F1 sample data
docker exec -it data-agent-api python -m da.scripts.load_data

# Run evaluations
docker exec -it data-agent-api python -m da.evals.run_evals --stats

# Test agent directly
python -m da.agent

# Format & validation (run from activated venv)
./scripts/format.sh
./scripts/validate.sh

# Deploy to Railway
./scripts/railway_up.sh
```

## The 6 Layers of Context

| Layer | Purpose | Source | Code |
|-------|---------|--------|------|
| **1. Table Metadata** | Schema, columns, types | `knowledge/tables/*.json` | `da/context/semantic_model.py` |
| **2. Human Annotations** | Metrics, rules, gotchas | `knowledge/business/*.json` | `da/context/business_rules.py` |
| **3. Query Patterns** | Validated SQL examples | `knowledge/queries/*.sql` | `da/context/query_patterns.py` |
| **4. Institutional Knowledge** | External context via MCP | Exa API (optional) | Configured in `da/agent.py` |
| **5. Memory** | Corrections, preferences | LearningMachine | Configured in `da/agent.py` |
| **6. Runtime Context** | Live schema inspection | `introspect_schema` tool | `da/tools/introspect.py` |

## Data Quality Gotchas (F1 Dataset)

| Issue | Tables Affected | Solution |
|-------|-----------------|----------|
| `position` is TEXT | `drivers_championship` | Use `position = '1'` (string comparison) |
| `position` is INTEGER | `constructors_championship` | Use `position = 1` (numeric comparison) |
| `date` is TEXT | `race_wins` | Use `TO_DATE(date, 'DD Mon YYYY')` for year extraction |

## Conventions

### Agent Pattern

The data agent follows this structure:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.knowledge import Knowledge
from agno.learn import LearningMachine, LearningMode
from db import db_url, get_postgres_db

agent_db = get_postgres_db(contents_table="data_agent_contents")

data_agent_knowledge = Knowledge(
    vector_db=PgVector(
        db_url=db_url,
        table_name="data_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    contents_db=agent_db,
)

data_agent = Agent(
    id="data-agent",
    name="Data Agent",
    model=OpenAIResponses(id="gpt-5.2"),
    db=agent_db,
    knowledge=data_agent_knowledge,
    learning=LearningMachine(...),
    search_knowledge=True,
    markdown=True,
)
```

### Database

- Use `get_postgres_db()` from `db` module
- **Important**: The `contents_table` parameter is only needed when the database is provided to a Knowledge base as a `contents_db`.

```python
# Agent WITH a Knowledge base - specify contents_table
agent_db = get_postgres_db(contents_table="data_agent_contents")

# Agent WITHOUT a Knowledge base - no contents_table needed
agent_db = get_postgres_db()
```

- Knowledge bases use PgVector with `SearchType.hybrid`
- Embeddings use `text-embedding-3-small`

### Imports

```python
# Database
from db import db_url, get_postgres_db

# Agent
from da import data_agent, data_agent_knowledge
```

## Adding Knowledge

### Table Metadata (`knowledge/tables/*.json`)

```json
{
  "table_name": "my_table",
  "table_description": "Description of the table",
  "table_columns": [
    {"name": "id", "type": "INTEGER", "description": "Primary key"},
    {"name": "name", "type": "TEXT", "description": "Name field"}
  ],
  "data_quality_notes": ["Important notes about data quirks"],
  "use_cases": ["When to use this table"],
  "related_tables": ["other_table"]
}
```

### Business Rules (`knowledge/business/*.json`)

```json
{
  "metrics": [
    {
      "name": "Metric Name",
      "definition": "What it measures",
      "table": "source_table",
      "calculation": "How to calculate"
    }
  ],
  "business_rules": [
    "Rule 1: Description"
  ],
  "common_gotchas": [
    {
      "issue": "Position column type varies",
      "tables_affected": ["drivers_championship", "constructors_championship"],
      "solution": "Check column type - TEXT vs INTEGER"
    }
  ]
}
```

### Query Patterns (`knowledge/queries/*.sql`)

```sql
-- <query name>top_race_winner_by_year</query name>
-- <query description>
-- Finds the driver with the most race wins in a given year.
-- Uses TO_DATE to parse the text date column.
-- </query description>
-- <query>
SELECT driver AS name, COUNT(*) AS wins
FROM race_wins
WHERE EXTRACT(YEAR FROM TO_DATE(date, 'DD Mon YYYY')) = 2019
GROUP BY driver
ORDER BY wins DESC
LIMIT 1;
-- </query>
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `EXA_API_KEY` | No | - | Exa API key for web research (Layer 4) |
| `PORT` | No | `8000` | API server port |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | `5432` | Database port |
| `DB_USER` | No | `ai` | Database user |
| `DB_PASS` | No | `ai` | Database password |
| `DB_DATABASE` | No | `ai` | Database name |
| `RUNTIME_ENV` | No | `prd` | Set to `dev` for auto-reload |

## Data Storage

| Data | Storage | Table/Location |
|------|---------|----------------|
| Vector embeddings | PostgreSQL (pgvector) | `data_agent_knowledge` |
| Document contents | PostgreSQL | `data_agent_contents` |
| F1 data tables | PostgreSQL | `race_wins`, `drivers_championship`, etc. |
| Session/memory | PostgreSQL | Automatic (Agno) |

## Ports

- API: 8000 (both Dockerfile and railway.json)
- Database: 5432

---

## Agno Framework Reference

### Model Providers

```python
# OpenAI (default in this project)
from agno.models.openai import OpenAIResponses
model = OpenAIResponses(id="gpt-5.2")

# Anthropic Claude
from agno.models.anthropic import Claude
model = Claude(id="claude-sonnet-4-5")

# Google Gemini
from agno.models.google import Gemini
model = Gemini(id="gemini-2.0-flash")

# Local models via Ollama
from agno.models.ollama import Ollama
model = Ollama(id="llama3")
```

### Knowledge & RAG

```python
from agno.knowledge import Knowledge
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector, SearchType

knowledge = Knowledge(
    name="My Knowledge Base",
    vector_db=PgVector(
        db_url=db_url,
        table_name="my_vectors",
        search_type=SearchType.hybrid,  # Recommended
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
    contents_db=get_postgres_db(contents_table="my_contents"),
    max_results=10,
)

# Use in agent
agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)
```

### Memory & Learning

```python
from agno.learn import (
    LearningMachine,
    LearningMode,
    LearnedKnowledgeConfig,
    UserMemoryConfig,
    UserProfileConfig,
)

agent = Agent(
    learning=LearningMachine(
        knowledge=my_knowledge_base,
        user_profile=UserProfileConfig(mode=LearningMode.AGENTIC),
        user_memory=UserMemoryConfig(mode=LearningMode.AGENTIC),
        learned_knowledge=LearnedKnowledgeConfig(mode=LearningMode.AGENTIC),
    ),
)

# Or simple agentic memory without full knowledge base
agent = Agent(enable_agentic_memory=True)
```

### Tools

```python
# SQL tools
from agno.tools.sql import SQLTools
tools = [SQLTools(db_url=db_url)]

# Custom tools
from agno.tools import tool

@tool
def my_tool(query: str) -> str:
    """Tool description.

    Args:
        query: The query parameter.

    Returns:
        Result string.
    """
    return f"Result: {query}"

agent = Agent(tools=[my_tool])
```

### Agent Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `id` | str | Unique identifier |
| `name` | str | Display name |
| `model` | Model | Language model to use |
| `db` | PostgresDb | Database for persistence |
| `instructions` | str | System prompt |
| `tools` | list | Available tools |
| `knowledge` | Knowledge | Knowledge base for RAG |
| `search_knowledge` | bool | Auto-search knowledge base |
| `learning` | LearningMachine | Learning configuration |
| `enable_agentic_memory` | bool | Track user preferences |
| `markdown` | bool | Format responses as markdown |

### Documentation Links

**LLM-friendly documentation (for fetching):**
- https://docs.agno.com/llms.txt - Concise overview of Agno framework
- https://docs.agno.com/llms-full.txt - Complete Agno documentation

**Web documentation:**
- [Agno Docs](https://docs.agno.com)
- [AgentOS Introduction](https://docs.agno.com/agent-os/introduction)
- [Tools & Integrations](https://docs.agno.com/tools/toolkits)
