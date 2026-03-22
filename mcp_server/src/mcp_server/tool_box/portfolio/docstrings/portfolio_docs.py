PORTFOLIO_GET_SUMMARY_V1 = """\
Returns the profile summary — the introductory section of the portfolio.

Use this first to get a high-level picture of who the person is before
drilling into specific sections.

Output includes:
- The section name (e.g. "About", "Profile")
- The full text of that section
- Word count

Example output:
  section: "About"
  content: "Full-stack engineer with 8 years of experience …"
  word_count: 120
"""

PORTFOLIO_LIST_SECTIONS_V1 = """\
Lists all sections found in the portfolio Markdown file.

Use this to discover what information is available before calling
portfolio_get_section or portfolio_search.

Output: ordered list of section names with word counts.

Example output:
  sections: [
    { name: "About",      word_count: 120 },
    { name: "Experience", word_count: 340 },
    { name: "Projects",   word_count: 210 },
    { name: "Skills",     word_count: 80  },
  ]
"""

PORTFOLIO_GET_SECTION_V1 = """\
Returns the full content of a named portfolio section.

The lookup is case-insensitive and matches prefix if an exact match is not
found (e.g. "exp" matches "Experience").

Parameters:
  section_name: The heading of the section to retrieve (e.g. "Experience").

Output: section name, full markdown content, word count.

Example:
  portfolio_get_section(section_name="Projects")
  → { name: "Projects", content: "### Project X …", word_count: 210 }
"""

PORTFOLIO_SEARCH_V1 = """\
Keyword search across all portfolio sections.

Use when you need to find specific information without knowing which section
it lives in (e.g. a technology, company name, or skill).

Parameters:
  query: One or more keywords to search for.

Output: list of matches, each with the section name and a ~240-character
excerpt centred on the match.

Example:
  portfolio_search(query="Python")
  → matches: [
      { section: "Skills",   excerpt: "… Python, TypeScript, SQL …" },
      { section: "Projects", excerpt: "… built in Python with FastAPI …" },
    ]
"""
