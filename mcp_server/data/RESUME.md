# Franco Donadio

## **Senior Full Stack Engineer | AI Engineer**

[LinkedIn](https://www.linkedin.com/in/francodonadio) | [GitHub](https://github.com/Frankietime)

donadiofranco7@gmail.com | +54 11 5859 5332 | Buenos Aires, Argentina / CDMX, Mexico

**Tech Summary:** Claude Code, GitHub Copilot, React, TypeScript, Redux, Zustand, Python, .NET Core, SQL Server, MCP, RAG, LLM Integration

---

## Summary

*Building at the intersection of engineering, AI, and creative technology*

Senior Full Stack Engineer with 10+ years building complex enterprise platforms in media marketing, FinTech, and data-intensive applications.

Currently building AI engineering systems with agentic architectures, MCP servers, and spec-driven development at Publicis Media.

R&D mindset for solving non-linear technical challenges: my skills are fully leveraged where innovative solutions require both **research and implementation**.

**Engineering Depth** — From UX to DB, I prioritize simplicity and elegance over cleverness, and I treat tech stacks as tools, not dogmas. Each context demands its own solution.

**Research-Driven Learning** — When a problem requires new knowledge, I design and execute a research path sustainable from short to long run. I prioritize a hands-on approach.

**Creative Intelligence** —  I bring original thinking to problem-solving and personal vision to project direction. 14+ years as a professional music composer for film, sound design, and jazz performer.

**Seeking:** AI Engineering, Full Stack Architecture, Creative Technology roles



## <br>

<br>

## Experience

### Senior AI Engineer — Distributed MCP Server Platform | [Publicis Media](https://www.publicisgroupe.com/)

**2025 – Present | Argentina, Mexico**

Distributed group of product-specific MCP servers powering two AI agents — **Marcel (MRCL)** and **OSA** — across different stages of the Publicis media planning and optimization ecosystem. Developing the Cross Media Optimizer MCP Server with an integration of shared PyPI libraries (core MCP infrastructure, JWT auth, distributed caching, token rate limiting, developer tooling).

**Product servers:** Cross Media Optimizer, Audience, Scenario Planner, Digital Optimizer, Insights

**Tech:** Python 3.13, FastMCP 2.x, FastAPI, Pydantic v2, boto3 (AWS SDK), Valkey | uv workspace | CI: Azure Pipelines | GitHub Copilot

**The Challenge:** Implementing workflows for managing media optimization project creation and project report data analysis/comparison. A single project/report has aprox. 150k tokens at least — exceeding most LLM context windows in a single read. The core challenge is implementing data processing and retrieval and processing techniques that optimize token usage, context window and reasoning across a large number of projects and reports within the same session.

**Achievements:**

- **+80% token saving** by implementing partial read/update operations and TOON format optimization
- Consulting tasks and in-company technical referent for MCP server development, LLM capabilities, token usage best practices, etc
- Architecture design and implementation for Cross Media Optimizer MCP Server
- Led knowledge transfer, onboarding and documentation craft on LLM and MCP capabilities for the engineering team
- Context management for large data, JSON-to-TOON format optimization, agent-directed data processing, prompting and workflow reinforcement

### Senior Full Stack Engineer — Cross Media Optimizer | [Publicis Media](https://www.publicisgroupe.com/)

**2019 – 2025 | Argentina, Mexico**

Media planning and optimization platform. Project configuration with demografic, campaign, inventory, vendor, budgets, and goals data for different scenarios (Optimization, Reach and Frequency, etc) + algorithm run over projects for performance prediction reports and buying recommendations.

**Phase 1 — Video Optimizer (2019–2023):** Angular, .NET Framework, EF, SQL Server

- Optimized Angular build and compile times **(~80% improvement)**
- System modularization: **84% reduction in AppModule size**, enabling lazy loading and tree-shaking
- Developed complex tree data structures for portfolio management with parent–child inheritance and overwrite logic

**Phase 2 — Cross Media Optimizer (2023–2025):** React, .NET Core, EF Core, SQL Server

- Contributed to front-end architecture: tech stack definition, coding guidelines, unit testing infrastructure
- **Rebuild Module** — Centralized data synchronization into a single reactive module. No bugs reported for this module after development
- **Portfolio Management** — Simplified system using binary math for data inheritance; reduced **70% of previous complexity**, eliminating nested conditionals
- **Demographic Target Services** — Refactored to a single normalized interface, reducing code by **50%** with caching and very low regression rate
- Reduced onboarding ramp time for new team members through mentoring and technical documentation

### Semi Senior Full Stack Engineer — Master Data Management | [Publicis Media](https://www.publicisgroupe.com/)

**2018 – 2019 | Argentina**

Master Data Management system ensuring consistency of domain information and data hierarchies for the Publicis enterprise ecosystem. Developed the React UI for data modeling, business rules, batch data ingestion with automated validation, and granular user permissions. Developed the middleware layer integrating with **Microsoft Master Data Services**, enabling CRUD workflows for entities consumed by other applications in the ecosystem.

**Tech:** React, Redux, .NET Framework, EF, SQL Server

**The Challenge:** Integrating Microsoft Master Data with the Publicis ecosystem through a Middleware Layer + Front End + API — generic enough to serve multiple consuming applications while maintaining stability and a low regression rate.

**Achievements:**

- Designed area-scoped Redux state management: each action is a meaningful app state transformation becoming a "clockwork mechanism" that proved to be optimal both for implementation and for fast a debugging process. Achieved **avg. 2 bugs/KLOC**
- Reduced boilerplate by **~40%** with reusable reducer utilities
- Architecture adopted and extended by 12+ contributors in subsequent iterations
- Full-stack: 70% front-end / 30% back-end, including backend unit testing
- In-company technical referent for React and Redux

### Junior Full Stack Engineer — Investran CRM | [SunGard / FIS (via Quadion)](https://www.fisglobal.com/)

**2015 – 2017 | Argentina**

CRM module development and maintenance for Investran, an enterprise investment platform for global financial institutions. AngularJS, jQuery, WebForms, NHibernate, SQL Server. Managed very large legacy codebases, improved workflows, and ensured compatibility with systems acquired by SunGard and later FIS.

---

## Other Projects

### AI Agent Development — Emotional Companion & Mithril (2025 – Present)

Full-stack AI chat platform with RAG pipeline using OpenAI embeddings + pgvector HNSW indexing. Auto-scaling chunking, semantic search, and database-driven prompt management powering two distinct agent personas.

**Tech:** Next.js, TypeScript, Drizzle ORM, PostgreSQL, Vercel AI SDK, OpenAI Embeddings, pgvector, Claude Code

- Built a Knowledge Base UI with document management, file upload, and semantic search testing with similarity scoring
- Google OAuth via NextAuth v5 with guest/regular user types

**Emotional Companion** — A calm, supportive space for emotional expression and reflection — at the intersection of technology, art, and emotional presence.

**Mithril — Dungeon Master Agent** — Old-school pen-and-paper RPG (BX/OSR style) agent bringing the spirit of 80s DIY roleplaying: world exploration, freedom of choice, real danger, and rich improvised storytelling.

### Candy Fight — Online Multiplayer Board Game (2025 – Present)

[GitHub](https://github.com/Frankietime/candyfight-boardgame)

Co-creator and lead engineer for the development of a digital board game inspired by _Dune Imperium: Rise of Ix_, implementing deck-building, worker placement, and resource management mechanics. Custom board game engine using React, TypeScript, boardgame.io, Zustand, and Node.js. Modular component architecture for creating game mod packages as plug-ins, with server-side game state, sockets, and multiplayer sync.

### Composer & Sound Designer — Film, TV & Interactive Media (2012 – Present)

[Demo Reel](https://www.youtube.com/watch?v=R1Jxx5ncKw8) | [Selected Works](https://soundcloud.com/franco-donadio/sets/selected-tracks)

14+ years as professional music composer, sound designer, and jazz performer. Collaborating with directors and creative teams on narrative identity, emotional arcs, and worldbuilding through sound.

### Indie Rock Soloist Project (2022 – Present)

[Spotify](https://open.spotify.com/intl-es/artist/0D6RxeqImnZDpTTOVb3foH) | [Linktree](https://linktr.ee/franichicle)

---

## Learning & Development

**Self-Directed Software Engineering | 2014 – Present**
Structured self-learning path in software engineering fundamentals, front-end architecture, clean code principles, design patterns, and systems thinking. Mentored by senior engineers at Publicis, Quadion, and FIS. Currently studying: AI Engineering, MCP, Agentic Architectures.

**Music Composition & Sound Design | 2012 – Present**
Professional training in composition, orchestration, sound design, and improvisation (jazz). The discipline of mastering music, learning jazz, practicing with patience across years, and building improvisation skills also shaped my mindset and intellectual skills.
Skills/Tools: Ensemble writing, Improvisation, Ableton, Pro Tools, Synthesizers, Max/MSP (visual programming environment for music, audio, and interactive media).

**Professional Jazz Musician | 2016 – Present**
The path to becoming a professional jazz player developed skills that directly transfer to engineering:

- Simplifying extremely complex material with patience trhough the years (e.g. working a single skill set for 3 years before moving to the next)
- Hearing others, relaxing and reacting only when necessary
- Knowing what to play as well as what not to play
- Decomposing difficult material into simple, small parts and learning in order with patience
- Building a second nature for improvisation — a fast, intuitive skill that shows up in real-time performance

---

## Skills

**Front-End**: Scalable UI architecture, modular component systems, complex state flows, interactive data-driven interfaces
*JS, TypeScript, React, Redux, Zustand, Angular, RxJS, Vite, Webpack, Vitest, Jest*

**UI/UX**: Intuitive, aesthetic, functional interfaces with focus on clarity and user flow

**Backend**: API development, middleware, layered architectures, domain modeling
*C#, .NET / .NET Core, Python, EF, Node.js, SQL Server, REST APIs*

**AI Engineering**: MCP Servers, RAG pipelines, LLM integration, Spec-Drive Development, Claude Code, AI Tools

**Testing**: Unit testing, test strategy design — Vitest, Jest, NUnit

**Soft Skills**: Clear communicator with strong technical articulation. Cross-disciplinary thinking. High creative capacity combined with engineering rigor. Strong ownership, discipline and initiative.

**Creative**: Film & games scoring, sound design for interactive experiences, art direction, game systems

---

## Languages

- **English:** Fluent
- **Spanish:** Native
