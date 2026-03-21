# MCP Instructions Design Framework

<!-- last-updated: 2026-03-19 -->

This document describes the framework used to design, author, and
extend MCP agent instructions (`mcp_server/src/mcp_server/instructions/instructions.py`).

---

## Overview

Agent instructions are a **layered intent recognition system** composed of four distinct layers,
each with a different cognitive role.

```
Intent recognition
  └─ Mental model         ← interpretive lens for reading ambiguous requests
  └─ Categories           ← the classification slots (use cases)
  └─ Procedural knowledge ← how to use this MCP server's capabilities
  └─ Examples             ← few-shot demonstrations of intent → action
```

The layers work in order: the mental model shapes how the agent reads
a request; categories classify it; procedural knowledge maps the
classification to tools; examples anchor the classification to real
user language.

---

## Layer 1 — Mental Model

### Purpose

Gives the agent an interpretive lens for domain-specific reasoning.
Without a mental model, the agent pattern-matches on surface phrasing.
With one, it can handle phrasing it has never seen before by reasoning
from first principles.

### Example model (generic)

Users reason in: **resources → operations → outcomes**

- Resources: the entities they work with (e.g., documents, records, jobs)
- Operations: the actions they can perform (create, read, update, delete, run)
- Outcomes: the results they care about (success/failure, data, metrics)

When a user's request is ambiguous, the agent applies this lens to
diagnose the underlying need before deciding on a tool chain.

### Design rules

- The mental model must be **domain-specific**, not generic AI reasoning.
- It should be expressible as a single sentence or simple structure.
  If it requires a paragraph to explain, it is too complex.
- It should generate **diagnostic questions** — things the agent asks
  itself to resolve ambiguity, not things it asks the user.

### When to extend

Add new diagnostic questions when:
- A category of ambiguous request repeatedly results in wrong classification.
- A new domain concept is introduced that changes the resources/operations/outcomes structure.

---

## Layer 2 — Categories

### Purpose

Categories are the **classification slots** that map user intent to
tools and tool chains. Every request must land in exactly one category before any
tool is called.

### Example categories (generic)

| # | Name | Core action |
|---|------|-------------|
| 1 | List & Discover | Browse and find available resources |
| 2 | Create & Configure | Create new resources with configuration |
| 3 | Modify & Iterate | Update existing resources and test variations |
| 4 | Analyze & Report | Retrieve and interpret results |
| 5 | Cross-Resource Comparison | Compare multiple resources side-by-side |
| 6 | Batch & Historical Analysis | Process multiple resources to find patterns |

### Design rules

- Categories must be **mutually exclusive** at the action level.
  It is acceptable for surface phrasing to be ambiguous across categories
  — that is what the Disambiguation Rules handle.
- Each category must have a defined set of tools or sequence of tool calls.
- Categories should be ordered from **lowest to highest complexity** and
  **most to least frequent** use. This signals priority to the agent.

### When to extend

Add a new category when:
- A new workflow type is identified that cannot be expressed as a
  variation of an existing category's tool chain.
- The new workflow is encountered frequently enough in production to
  warrant its own classification slot (not just an Indirect Intent Pattern).

Do not add a category for every edge case. Edge cases belong in
Indirect Intent Patterns.

---

## Layer 3 — Procedural Knowledge

### Purpose

Procedural knowledge defines **how to execute** each category: the
tool chains, sequencing rules, guard rails, and async handling patterns.
This is the implementation layer — the agent's "how."

### Structure

Each category's procedural knowledge has two parts:

1. **Tool chain** — the ordered sequence of tool calls, including
   branching paths.

2. **Rules** — behavioral constraints that must be respected during
   execution. Rules address the most common failure modes specific to
   that category.

### Design rules

- Tool chains must reference **only active, registered tools**.
  Uncertain or disabled tools must not appear in any chain.
- Each rule should have a clear triggering condition.
- Async patterns must be explicit. Any tool that is asynchronous must
  have its polling pattern documented in the procedural rules.
- The Critical Behavioral Rules section documents **cross-category**
  constraints that apply regardless of which category is active.

### When to extend

Add or update procedural knowledge when:
- A new tool is registered (add it to the relevant tool chain).
- An existing tool's behavior changes (update the affected rules).
- A new async pattern is introduced (document polling behavior).
- A failure mode is discovered in production (add a guard rule).

---

## Layer 4 — Examples

### Purpose

Examples are **few-shot demonstrations** that ground the agent's
classification in real user language. They bridge the gap between
the abstract category structure and the specific, idiomatic phrasing
users actually use.

### Structure

Three example types are used:

| Type | Table | Role |
|------|-------|------|
| Direct Intent Map | User phrase → Category → Inferred action | Unambiguous phrasings — the agent should classify these without hesitation |
| Indirect Intent Patterns | User phrase → Business need → Category | Surface request masks a multi-step workflow — requires business need diagnosis |
| Disambiguation Rules | Ambiguous phrase → Could be → Resolve by | Phrases that map to more than one category — resolved by resource state or context |

### Design rules

- Direct Intent Map rows should cover the **most frequent and
  unambiguous** phrasings for each category. Do not pad with rare cases.
- Indirect Intent Patterns are for phrases where the surface request
  and the correct action are **semantically distant**. If the surface
  phrase clearly implies the action, it belongs in the Direct Intent Map.
- Disambiguation Rules exist only for phrases that **genuinely map to
  multiple categories** and where the two interpretations lead to
  meaningfully different tool chains. Do not add disambiguation rules
  for clarity — add them for real conflicts.

### When to extend

Add rows to any example table when:
- A real user phrasing is observed in production that is not covered by an existing row.
- A misclassification event is traced back to missing coverage in a specific table.

Remove rows when:
- A category is removed or merged.
- A phrasing is found to be misleading or to conflict with a rule.
