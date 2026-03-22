MD_LIST_SECTIONS_V1 = """\
List all section headings in a Markdown document with their word counts.

Use this tool before md_query when the search term is uncertain or the user's
question is ambiguous. Inspect the heading names, then pass the exact heading
(or a key term from it) as search_term to md_query for a precise retrieval.

Workflow:
  1. md_list_sections(document=...) → see available sections
  2. md_query(document=..., search_term=<heading or key term>) → get full content

Returns sections in document order with word counts so you can judge which
section is likely to contain the answer before reading it.
"""

MD_QUERY_V1 = """\
Read a Markdown file and return the sections most relevant to a search term.

Use this tool when the user asks a question whose answer lives in a known Markdown
document. Extract a search term from the user's intent, supply the absolute path to
the file, and the tool returns the best-matching sections as full plain-text content —
ready to use directly as context in your answer.

Scoring uses BM25 (lexical ranking — no embeddings, no vector database). Sections
whose *heading* contains the search term are weighted more heavily than sections that
only mention it in the body text.

When to use:
  - "What does the doc say about authentication?" → search_term="authentication"
  - "How do I configure the database?" → search_term="database configuration"
  - "Explain the deployment process" → search_term="deployment"

Returns an empty section list (not an error) when no section matches the search term.
Try a broader or alternative term and call again.
"""
