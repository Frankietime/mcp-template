# Tools Best Practices

<!-- last-updated: 2025-03-17 -->

> *MCP Servers are User Interfaces (for Agents)*
> 

> *Python Zen: Simple is better than complex. Complex is better than complicated. Flat is better than nested.*
> 

## Intro

Tools are a new kind of software which reflects a contract between deterministic systems and non-deterministic agents. 

Our goal is to increase the surface area over which agents can be effective in solving a wide range of tasks by using tools to pursue a variety of successful strategies. Fortunately, tools that are most “ergonomic” for agents also end up being surprisingly intuitive to grasp as humans.

For example, Claude Code is built with simple tools that mimic what a human developer would do. The tools are:

- Read Files
- Grep / Glob
- Edit
- Bash
- WebSearch / WebFetch (delegado a subagent Haiku)
- TodoRead / TodoWrite (task management)
- Task (delegate tasks to subagents)

It can be difficult to anticipate which tools agents will find ergonomic and which tools they won’t without getting hands-on yourself.

## Tool Design

Tool design is about building workflows that hide plumbing and show outcomes, and making powerful operations simple to execute and understand. Instead of mirroring API endpoints, design tools that represent a complete user action.

More tools don’t always lead to better outcomes. A common error is to build tools that merely wrap existing software functionality or API endpoints—whether or not the tools are appropriate for agents. This is because agents have distinct “affordances” to traditional software—that is, they have different ways of perceiving the potential actions they can take with those tools.

LLM agents have limited "context" (that is, there are limits to how much information they can process at once), whereas computer memory is cheap and abundant. Consider the task of searching for a contact in an address book. Traditional software programs can efficiently store and process a list of contacts one at a time, checking each one before moving on.

However, if an LLM agent uses a tool that returns ALL contacts and then has to read through each one token-by-token, it's wasting its limited context space on irrelevant information (imagine searching for a contact in your address book by reading each page from top-to-bottom—that is, via brute-force search). The better and more natural approach (for agents and humans alike) is to skip to the relevant page first (perhaps finding it alphabetically).

Tools should enable agents to subdivide and solve tasks in much the same way that a human would, given access to the same underlying resources, and simultaneously reduce the context that would have otherwise been consumed by intermediate outputs.

Too many tools or overlapping tools can also distract agents from pursuing efficient strategies. Careful, selective planning of the tools you build (or don’t build) can really pay off.

In the process of designing an MCP Server, which includes a fair amount of try and error, ruthlessly curate and limit the toolset to 5–15 high-value tools. Too many tools confuse agents and waste tokens.

In the same vein, tool implementations should take care to return only high signal information back to agents. They should prioritize contextual relevance over flexibility, and eschew low-level technical identifiers 

Even your tool response structure—for example XML, JSON, or Markdown—can have an impact on evaluation performance: there is no one-size-fits-all solution.

Implementing some combination of pagination, range selection, filtering, and/or truncation with sensible default parameter values for any tool responses that could use up lots of context. For Claude Code, tool responses are restricted to 25,000 tokens by default. The effective context length of agents is expected to grow over time, but the need for context-efficient tools also to remain.

Because agents often retry on failure, ensure your tool calls are idempotent—calling them twice with the same data does not cause issues and explicitly flag them as idempotent. 

## Everything is a prompt

This means that function and argument names, along with their accompanying docstrings and annotations, are not just code—they are direct instructions that shape an agent's understanding. This philosophy extends to tool responses, which should be viewed as the agent's next prompt rather than a final output. By treating responses as guidance, you can implement progressive disclosure of information; as the tool code runs, it can collect context and generate useful errors that point toward proper system usage. 

By letting the agents ask for different levels of output detail, you can reveal information only when needed, ensuring the agent remains focused and efficient throughout the workflow.

## Token Budget and Monitoring

Before creating a tool, you should allocate a token budget—either mentally or as an explicit feature—to serve as a strict operational guide. Tools must never exceed this limit, and guardrails should be implemented to truncate data and restrict tokens within tool responses. By consistently optimizing for token usage and reporting these metrics with transparency, you improve technical performance while building greater confidence in the reliability of your AI tools.

## Tool Evaluation

Next, you need to measure how well your agent uses your tools by running an evaluation. Start by generating lots of evaluation tasks, grounded in real world uses.

Each evaluation prompt should be paired with a verifiable response or outcome.

For each prompt-response pair, you can optionally also specify the tools you expect an agent to call in solving the task, to measure whether or not agents are successful in grasping each tool’s purpose during evaluation. 

We recommend running your evaluation programmatically with direct LLM API calls. Use simple agentic loops (`while`-loops wrapping alternating LLM API and tool calls): one loop for each evaluation task. Each evaluation agent should be given a single task prompt and your tools.

In your evaluation agents’ system prompts, we recommend instructing agents to output not just structured response blocks (for verification), but also reasoning and feedback blocks. Instructing agents to output these *before* tool call and response blocks may increase LLMs’ effective intelligence by triggering chain-of-thought (CoT) behaviors.

As well as top-level accuracy, we recommend collecting other metrics like the total runtime of individual tool calls and tasks, the total number of tool calls, the total token consumption, and tool errors. Tracking tool calls can help reveal common workflows that agents pursue and offer some opportunities for tools to consolidate.

To build effective tools for agents, we need to re-orient our software development practices from predictable, deterministic patterns to non-deterministic ones.

# Sources

https://www.youtube.com/watch?v=96G7FLab8xc

https://www.anthropic.com/engineering/writing-tools-for-agents

https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use#best-practices-for-tool-definitions

https://engineering.block.xyz/blog/blocks-playbook-for-designing-mcp-servers

https://medium.com/@kelly.kohlleffel/what-i-learned-building-mcp-servers-unifying-my-entire-data-stack-into-a-single-intelligent-ui-28cf0f088a2a

https://www.youtube.com/watch?v=RFKCzGlAU6Q

https://blog.bytebytego.com/p/how-cursor-shipped-its-coding-agent?utm_campaign=post-expanded-share&utm_medium=web&triedRedirect=true