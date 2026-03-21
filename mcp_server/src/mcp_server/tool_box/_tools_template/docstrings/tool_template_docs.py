"""Versioned docstrings for tool_template.

Naming convention: TOOL_NAME_V{version}
Active version is registered in __init__.py
"""

TOOL_TEMPLATE_V1 = """
# Docstrings (descriptions) Best practices
------------------------------------------

## Markdown Format

Models are largely trained on markdown formatted data and perform better when reading markdown formatted prompts.
For illustration purposes, this docstring is formatted as markdown.

[Markdown Basic Syntax](https://www.markdownguide.org/basic-syntax/)

## Examples

Examples are **contracts of behaviour**.
Prefer showing examples rather than relying on abstract explanations or indications.

_(!) Be careful because agents stick to examples' implicit patterns_
_(i.e. if you provide 2 columns in an example, the agent will stick to showing 2 columns approx., never 10)_

Use markdown bullets to give clear instructions and steps.

Examples can show:
- how a successful process should be
- how the data should look like
- what concrete outcomes or situations to expect
- how it looks like to successfully accomplish the task at hand.

One example could illustrate how returned non-JSON data will look like and how to parse it:

    Returns the completed resource list.
    Data is in TOON format (2-space indent, arrays show length and fields).

        ```toon
            resources[3]{id,name,status,created_at}:
            1,Resource Alpha,active,2026-01-15T10:30:00Z
            2,Resource Beta,inactive,2026-01-14T15:22:00Z
            3,Resource Gamma,active,2026-01-13T09:45:00Z
        ```

    You MUST show the user a table with all the resources:

    [RESOURCES] // Markdown Table
    | id   | name           | status   | tags           |
    | 1    | Resource Alpha | active   | tag1, tag2     |
    | 2    | Resource Beta  | inactive | tag3           |
    | 3    | Resource Gamma | active   | tag1, tag4     |
"""


TOOL_TEMPLATE_V2 = """
# Resource Information Tool

Returns information for a given resource by ID.

## When to Use
- User asks for resource details or configuration
- Need to inspect current resource state before modifications

## Output Format
Returns structured resource data including:
- Resource metadata (id, name, status)
- Associated tags
- Operational metadata

## Example Response Table
| id   | name           | status | tags       |
|------|----------------|--------|------------|
| 1928 | Resource Alpha | active | tag1, tag2 |
| 9381 | Resource Beta  | active | tag3       |
"""
