---
name: skill-finder
description: >
  Use whenever the user asks how to set up, configure, deploy, or use a
  specific tool, framework, library, or cloud service — or when you encounter
  an unfamiliar technology and need a best-practice guide. Trigger whenever the
  user mentions tools like Kubernetes, Terraform, Docker, AWS, React, PostgreSQL,
  Redis, Grafana, GitHub Actions, or any of 89K+ other technologies. Also use
  when the user explicitly asks to search, find, or browse available skills.
---

# Skill Finder

89,000+ searchable expert guides. Search → fetch → apply.

## Quick Reference

| Action | Endpoint |
|--------|----------|
| Semantic search | `GET /api/search?q=...&k=3` |
| Keyword search | `GET /api/search/keyword?q=...&limit=5` |
| Fetch full guide | `GET /api/skills/{id}` |
| Browse categories | `GET /api/categories` |

Base URL: `https://zcheng256-skill-retrieval.hf.space`

## Workflow

### 1. Search

Extract technology + task, URL-encode spaces as `+`:

```
WebFetch("https://zcheng256-skill-retrieval.hf.space/api/search?q=kubernetes+deployment&k=3")
```

Response: `[{"id": "a1b2", "name": "...", "description": "...", "score": 0.81, ...}]`

If semantic search returns low scores (< 0.5) or irrelevant results, try keyword:

```
WebFetch("https://zcheng256-skill-retrieval.hf.space/api/search/keyword?q=terraform+aws&limit=5")
```

### 2. Fetch

Pick the result with the highest score and most relevant description:

```
WebFetch("https://zcheng256-skill-retrieval.hf.space/api/skills/SKILL_ID")
```

Response includes `instructions` — the complete step-by-step guide.

### 3. Apply

Follow the `instructions` directly to complete the user's task.
Do NOT summarize them. Apply as your own knowledge.

## Common Mistakes

- **Summarizing instead of applying.** The fetched instructions are meant to be
  followed, not reported back. Execute the steps, don't describe them.
- **Searching too broadly.** `"how to code"` returns noise. Be specific:
  `"fastapi websocket authentication"` beats `"python web framework"`.
- **Ignoring keyword search.** If you know the exact tool name, keyword search
  is faster and more precise than semantic search.
- **Skipping verification.** After applying a guide, verify the result works.
  Don't assume the instructions are complete for the user's specific context.
