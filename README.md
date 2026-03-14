# skill-finder

> One skill to unlock 89,000.

An agent skill that gives Claude Code, Codex CLI, and any skill-compatible agent instant access to a knowledge base of **89,267 expert guides** — covering tools, frameworks, cloud platforms, DevOps, ML, databases, and more.

No local setup. No MCP. Just drop in the skill and go.

## How It Works

```
You: "How do I deploy to Kubernetes?"
                ↓
       skill-finder triggers
                ↓
   Agent searches 89K guides via API
                ↓
    Fetches best match (full instructions)
                ↓
   Agent follows the guide to complete your task
```

The agent experience is seamless — it searches, fetches, and applies the right guide as if it always knew how.

## Install

### Claude Code

```bash
cp -r skill-finder/ ~/.claude/skills/skill-finder/
```

### Codex CLI / Goose / Amp

```bash
cp -r skill-finder/ ~/.agents/skills/skill-finder/
```

That's it. No API keys, no dependencies, no configuration.

## What's Inside

```
skill-finder/
├── SKILL.md              # The skill — agents load this
├── scripts/
│   └── serve.py          # Self-hosted API server (optional)
└── Dockerfile            # Deploy your own instance (optional)
```

- **SKILL.md** is all you need. It calls a hosted API at `zcheng256-skill-retrieval.hf.space`.
- **scripts/serve.py** is the API server source — self-contained, no MCP dependency. Deploy your own if you want full control.

## Knowledge Base

89,267 skills sourced from:

| Source | Skills | Examples |
|--------|--------|----------|
| LangSkills | 72K+ | Tool guides, framework workflows, deployment patterns |
| Anthropic Official | 50+ | PDF, PPTX, DOCX, algorithmic art, MCP builder |
| Community | 200+ | Superpowers, custom workflows |
| SkillNet | 16K+ | Research-derived task skills |

Covers: Kubernetes, Terraform, Docker, AWS, GCP, React, Python, Rust, PostgreSQL, Redis, Grafana, GitHub Actions, and thousands more.

## skill-finder vs skill-retrieval-mcp

This project is the **zero-setup** companion to [skill-retrieval-mcp](https://github.com/JayCheng113/skill-retrieval-mcp). Same knowledge base, different integration approach.

| | **skill-finder** | **[skill-retrieval-mcp](https://github.com/JayCheng113/skill-retrieval-mcp)** |
|---|---|---|
| **What it is** | A single skill file (SKILL.md) | An MCP server |
| **Setup** | Copy one file | `pip install` + download 1.1GB data + register |
| **Runs where** | Cloud API (hosted) | Local (your machine) |
| **Requires MCP** | No | Yes |
| **Agent support** | Any agent with skills + WebFetch | MCP-compatible agents only |
| **Latency** | ~200ms (network) | <5ms (local) |
| **Custom skills** | No (uses hosted DB) | Yes (import your own) |
| **Offline** | No | Yes |

**Choose skill-finder** if you want instant access with zero setup.
**Choose [skill-retrieval-mcp](https://github.com/JayCheng113/skill-retrieval-mcp)** if you need local speed, offline access, or custom skills.

## Self-Hosting

Want to run your own API? The server is a single Python file with zero MCP dependency:

```bash
pip install starlette uvicorn faiss-cpu numpy sentence-transformers huggingface-hub

# Data downloads automatically on first run
python scripts/serve.py
```

Or deploy via Docker:

```bash
docker build -t skill-finder .
docker run -p 7860:7860 skill-finder
```

Update the API URL in SKILL.md to point to your instance.

## API

| Endpoint | What it does |
|----------|-------------|
| `GET /api/search?q=...&k=5` | Semantic search (returns summaries with scores) |
| `GET /api/skills/{id}` | Full skill instructions by ID |
| `GET /api/search/keyword?q=...&limit=10` | Keyword search (FTS5) |
| `GET /api/categories` | List all categories and counts |
| `GET /api/health` | Server status |

## License

MIT
