# Franco Donadio
## **Senior Full Stack Engineer | AI Engineer**

[LinkedIn](https://www.linkedin.com/in/francodonadio) | [GitHub](https://github.com/Frankietime)

donadiofranco7@gmail.com | +54 11 5859 5332 | Buenos Aires, Argentina / CDMX, Mexico

**Tech Summary:** Claude Code, GitHub Copilot, React, TypeScript, Redux, Zustand, Python, .NET Core, SQL Server, MCP, RAG, LLM Integration

---

## Summary

*Building at the intersection of engineering, AI, and creative technology*

10+ years of experience building complex enterprise platforms in media marketing optimization, FinTech, and data-intensive applications.

Currently working in the media marketing domain, building AI Engineering systems and using Spec-Driven Development for agentic coding: implementing Agents with different retrieval strategies and Model Context Protocol (MCP) servers for complex data environments that require token optimization.

Background as a professional composer and sound designer for film brings a unique lens to systems design — pattern recognition, improvisation, and non-linear problem solving.

### Unique Value Proposition

#### The Intersection of Engineering, Research, and Creativity in Systems Design

R&D mindset for solving non-linear technical challenges: my skills are fully leveraged where innovative solutions require both research and implementation.

**Engineering Depth** — From UX to DB and distributed systems. I prioritize simplicity and elegance over cleverness, and I treat tech stacks as tools, not dogmas. Each context demands its own solution.

**Creative Intelligence** — I bring original thinking to problem-solving and personal vision to project direction. 14+ years as a professional music composer for film, sound designer, and jazz performer.

**Research-Driven Learning** — When a problem requires new knowledge, I design and execute my own learning path, sustainable from days or months to years. I prioritize a hands-on approach (prototyping, POCs, applied knowledge).

**Seeking:** AI Engineering, Full Stack Architecture, Creative Technology roles

---

## Experience

### Senior AI Engineer — Distributed MCP Server Platform | [Publicis Media](https://www.publicisgroupe.com/)

**2025 – Present | Argentina, Mexico**

#### Description

Distributed group of product-specific MCP servers powering two AI agents across different stages of the Publicis media planning and optimization ecosystem. Developing the Cross Media Optimizer MCP Server with the integration of shared PyPI libraries providing reusable infrastructure across all servers (core MCP infrastructure, JWT auth, distributed caching, token rate limiting, and developer tooling).

**AI Agents:**
- **Marcel (MRCL)** and **OSA** — two AI agents that leverage the server group across different stages of analysis and media optimization workflows

**Shared packages:**
- **pmos_shared_mcp** — Core MCP infrastructure (FastMCP, FastAPI, boto3, Valkey caching)
- **pmos_shared_auth** — JWT token handling, token exchange, and caching (PyJWT, httpx, cryptography)
- **pmos_shared_tooling** — Developer tooling for MCP workflows (OpenAI SDK, MCP CLI, Rich)
- **pmos_shared_testing** — Automated testing utilities for MCP servers

**Product Servers** — AI-accessible tools for agents to interact with media planning and optimization workflows:
- **Cross Media Optimizer** — Managing media optimization projects, results, analysis, and optimization runs
- **Audience**
- **Scenario Planner**
- **Digital Optimizer**
- **Insights**

#### Tech Stack

Python 3.13, FastMCP 2.x, FastAPI, Pydantic v2 | uv workspace (multi-package monorepo)

- **AWS:** boto3 SDK, Secrets Manager — deploys on AWS Bedrock
- **Caching:** Valkey (Redis-compatible distributed cache)
- **Auth:** PyJWT, httpx, cryptography
- **AI/LLM:** OpenAI SDK, MCP CLI 1.26+
- **CI/CD:** Azure Pipelines | GitHub Copilot
- **Quality:** Ruff, pytest-asyncio, commitizen, pre-commit

#### The Challenge

Implementing workflows for managing media optimization project creation and project report data analysis/comparison. A single project/report has aprox. 150k tokens at least — exceeding most LLM context windows in a single read. The core challenge is implementing data processing and retrieval and processing techniques that optimize token usage, context window and reasoning across a large number of projects and reports within the same session.

#### Achievements

- **+80% token saving** by implementing partial read/update operations and TOON format optimization

- Consulting & Design
  - Consulting tasks and in-company technical referent for MCP server development, LLM capabilities, token usage best practices
  - Architecture design and implementation for Cross Media Optimizer MCP Server
  - Led knowledge transfer, onboarding and documentation craft on LLM and MCP capabilities for the engineering team

- Research and Development (R&D) + POCs:

  - Context Management for large data, token optimization, agent-directed data processing

  - Format optimization from JSON to TOON, specially for non-nested tabular data (uniform and non-uniform)

  - Description, naming, tool result format and prompting best practices and workflow reinforcement

### Senior Full Stack Engineer — Cross Media Optimizer | [Publicis Media](https://www.publicisgroupe.com/)

**2019 – 2025 | Argentina, Mexico**

#### Description

Media planning and optimization platform that helps project planners navigate the complex landscape of multi-channel media buying. Users configure project parameters based on their target audiences, campaign dates, available inventory across media types and vendors, budget constraints, and performance objectives. The system employs optimization algorithms to generate strategic buying recommendations that balance reach, frequency, cost efficiency, and goal achievement across potentially thousands of inventory combinations, with flexible result visualization that adapts based on the level of specificity in the campaign configuration.

#### **Phase 1 — Video Optimizer (2019–2023)**

#### Tech Stack

Angular, .NET Framework, Entity Framework, Microsoft SQL Server

#### The Challenge

To build the next generation of media marketing optimizers. UI/UX Implementation for planning different kinds of projects (Optimization, Reach & Frequency, etc.) and reporting visualization. Development of complex and rich-featured user interface. Some of the features included:

- Multi-level work contexts based on Agency, Client, and Region

- Project & Portfolio (Subproject Management)

  - Optimization projects and sub-projects for media planning

  - Parent–child relationships

    - Inherited configuration from parent projects

    - Override and validation rules per hierarchy level

    - Hierarchical project structures with propagation of changes

- External Data Integration (support for different providers + data normalization for internal consumption)

- Optimization Execution & Results Report

#### Achievements

- Optimization of Angular build and compile times **(~80% improvement)**
- Implementation of code guidelines and consulting
- System Modularization, HMR:
- **84% reduction in AppModule size**
- Proper separation of concerns
- Foundation for lazy loading (better performance)
- Better tree-shaking
- Visualization and complex propagation of changes across tree data structures (Portfolio Management) + parent–child inheritance and overwrite logic


#### Research & Development

System modularization and HMR for enhancing overall build times and performance

#### **Phase 2 — Cross Media Optimizer (2023–2025)**

Migration of Video Optimizer legacy software to Cross Media Optimizer for modernization and tech stack compliance with the application ecosystem.

#### Tech Stack

React, .NET Core, Entity Framework Core, Microsoft SQL Server

#### The Challenge

- Migrate legacy system built in Angular + .NET to React + .Net Core
- Re-design of solutions where legacy code proved high complexity and low quality

#### Achievements

- **Consulting / Architecture**

  - Risk mitigation advice over team composition, overall project complexity, development times, key points of refactor, and how to implement the new designs

  - Contributed to the front-end architecture by defining tech stack, coding guidelines, and unit testing infrastructure implementation

  - Reduced onboarding time for new team members through mentoring and development of technical documentation


- **Rebuild module**

  - Reduced system complexity by resolving data synchronization issues within the same project, avoiding dispersed and poorly maintainable synchronization logic (Angular).

  - Synchronization **bugs were reduced to zero**, and responsibility was assigned to a single module (previously dispersed among components).

  - By leveraging the React life cycle, cases were found where the state was modified unnecessarily: if the Rebuild runs more than once, it is because there is a bug.

  - The engineering team never again had to worry about developing logic within a component that needs to know what is happening in another component; the Rebuild Module reacts to data changes to re-compute the project state.

  - **No bugs reported for this module after development**


- **Portfolio Management Module**
  Within the projects, brands and products are defined. This allows generating nesting for each step of the project. For example, the Demographic Targets Step can now have data defined at the All Brands level, specific Brand, All Products, and specific Brand + Product, with a data inheritance logic (writing data at one tree level can impact another level), overwrite warning, restoration, and validations. **The system was drastically simplified** by adding binary math to calculate the origin of data inheritance and overwriting. On this basis, **70% of the previous system's complexity was reduced**, including, for example, all nested conditionals. UI components that consume the Portfolio service were also developed.
  Bugs that emerged in a timespan of 1 month were the only bugs reported for this functionality.

- **Demographic Target Services Refactor**
  The number of lines was **reduced by 50%**, and the functionality was organized into a single class responsible for managing the complexity of integrating different target sources (which have different data structures and IDs structures), delivering a simple and homogeneous interface to the rest of the components that consume it with a normalized "Target" entity. At the same time, since targets are required in different parts of the application, caching logic was developed to avoid multiple calls to the different APIs. In this way, the maintainability and testability of the code were drastically improved, reducing the overall complexity of the system. **Very low regression rate**, only in the following sprints after development.

### Semi Senior Full Stack Engineer — Master Data Management (MDM) | [Publicis Media](https://www.publicisgroupe.com/)

**2018 – 2019 | Argentina**

#### Description

Master Data Management for the Publicis Ecosystem's business data. The system ensures that domain information and data hierarchies remain consistent across all enterprise systems by providing a unified interface for defining data structures, enforcing business rules, and user permissions. Users can design the structure for entire models, upload and process data in batches with automated validation, define sophisticated conditional logic for enforcing data quality standards without manual intervention, and provide a granular user permission model. The platform orchestrates the synchronization with an underlying Microsoft Master Data instance using a middleware solution while abstracting its intricacies behind a user-friendly front end and a proper backend API.

Worked on the middleware layer integrating with **Microsoft Master Data Services**, enabling CRUD workflows for entities to be consumed by other applications in the ecosystem.

#### Tech Stack

React, .NET Framework, Entity Framework, Microsoft SQL Server, Microsoft Master Data

#### The Challenge

Integrate the Microsoft Master Data solution with the Publicis Ecosystem through the development of a Middleware Layer + Front End + API. As the main data source for the entire Publicis Ecosystem, this solution had to be both sufficiently generic to offer a consumable API for several applications and stable with a low regression rate.

#### Achievements

- Achieved an avg. of 2 front-end bugs per KLOC rate.
- In-company technical referent for React and Redux

- **Front End & Redux Architecture**
  Designed and implemented the Front End architecture and Redux state management. The Redux implementation introduces an area-scoped UI state management system where loading states, errors, and modals are tracked independently from specific ui view modes, ui data and flags across 15+ screen sections, a pattern that prevents UI conflicts and ambiguities in a complex SPA.
  - Achieved extremely low front end incident rates (**avg. 2 bugs/KLOC**) in comparison of other projects of the same size.
  
  - Very easy debug process by proper use of action events. This enabled us to simply look at the system like a **clockwork mechanism** in which each "tic" represented a meaningful app state transformation.
  
  - UI State Tree Design: **clear separation of concerns** (ui, ui logic, errors, etc) inside front end's state tree, making it easy to look for checking errors or inconsistencies.
  
  - Common functionality is abstracted into reusable reducer utilities, which **reduced boilerplate by ~40%** while enabling any team member to extend the codebase without understanding the entire system.
  
  - Centralized error handling (including session expiration routing and debug logging).
  
  - Architectural decisions persisted as my team passed the project to other hands to continue the development of the Video Optimizer project. These development patterns become leveraged and extended by other 12 contributors.

### Junior Full Stack Engineer — Investran CRM | [SunGard / FIS (via Quadion)](https://www.fisglobal.com/)

**2015 – 2017 | Argentina**

Worked on the CRM module and maintenance of **Investran**, an enterprise investment platform used by global financial institutions. Delivered features using **AngularJS, jQuery, WebForms, NHibernate**, and SQL Server. Managed legacy codebases, improved workflows, and ensured compatibility with systems acquired by SunGard and later FIS.

---

## AI Side Projects

### AI Agent Development (Emotional Companion, Mithril)

#### Tech Stack

Next.js, TypeScript, Drizzle ORM, PostgreSQL, Vercel AI SDK, OpenAI Embeddings, pgvector, Claude Code

#### Core Platform Engineering

  - Designed and built full-stack AI chat application with Next.js, React, Vercel AI SDK, and PostgreSQL (Neon)
  - Implemented real-time streaming responses with resumable stream support
  - Integrated multi-provider LLM routing (OpenAI, xAI Grok, Kimi K2) via Vercel AI Gateway and OpenRouter

#### Retrieval-Augmented Generation (RAG) Pipeline

  - Engineered a vector-based knowledge system using OpenAI embeddings (1536-dim) with pgvector HNSW indexing
  - Implemented auto-scaling chunking strategies based on document size (1K–4K char chunks with overlap)
  - Built a Knowledge Base UI with document management, file upload, and a semantic search query playground with similarity scoring
  - Supported formats: text, markdown, CSV, and PDF

#### Personality & Prompt Engineering

  - Created a database-driven system prompt management system with active/inactive switching
  - Authored detailed personality prompts (Dungeon Master with rules-grounded RAG; Emotional Companion with ethical guardrails)

#### Auth, Testing & DevOps

  - Implemented Google OAuth authentication via NextAuth v5 with guest/regular user types

#### **Emotional Companion Agent**

**2025 – Present**

A calm, supportive space for emotional expression and reflection — at the intersection of technology, art, and emotional presence.

**Core principles:**

- **Emotional safety** — Non-judgmental, no urgency or pressure
- **Minimal interaction** — Short, gentle responses; silence and pauses respected
- **Multisensory atmosphere** — Text, optional voice, and subtle visual backgrounds
- **Ethical guardrails** — No diagnoses, prescriptive advice, or manipulation

#### **Mithril — Dungeon Master Agent**

**2025 – Present**

Old-school pen-and-paper RPG (BX/OSR style) agent bringing the spirit of 80s DIY roleplaying: world exploration, freedom of choice, real danger, and rich improvised storytelling.

**Core principles:**

- **Living world** — Consequences emerge from player choices, not railroaded narratives
- **Rules-grounded** — Uses RAG to retrieve and apply game rules consistently
- **Rich narration** — Immersive descriptions with intentional pacing and formatting
- **Adaptive play** — Learns from player style, improvises new adventures from existing material

The Dungeon Master draws from rules databases, literary sources, and adventure modules to create coherent, memorable sessions.

---

### MCP Server Template — Open Source Scaffold (2025 – Present)

[GitHub](https://github.com/Frankietime/mcp-template)

#### Description

Production-ready scaffold for building Model Context Protocol servers with Python and FastMCP. Designed to serve three purposes: a functional MCP server starter, an onboarding resource for engineers new to MCP, and a reference codebase for AI agents.

#### Tech Stack

Python, FastMCP, Pydantic-AI, uv (workspace)

#### Design Patterns & Achievements

- Shared response builders (`SummaryResponse`, `ErrorResponse`) standardizing tool outputs across the server
- Docstring and tool name registries preventing typos and enabling safe refactoring
- TOON format serialization for token-optimized LLM consumption
- Pydantic-AI agent for interactive terminal testing + agentic integration test suite
- Comprehensive internal documentation on tool design, agent instruction frameworks, and workspace management

---

## Other Projects

### Candy Fight — Online Multiplayer Board Game (2025 – Present)

[GitHub](https://github.com/Frankietime/candyfight-boardgame)

#### Description

Co-creator and lead engineer of a digital board game inspired by _Dune Imperium: Rise of Ix_, implementing deck-building, worker placement, and resource management mechanics. Developed in collaboration with a **three-person team**, we work together in game mechanics, story elements, visual identity and art direction.

Modular component architecture for creating game mod packages as plug-ins using combinations of custom components.

Built UI/UX for complex turn-based interactions and server-side logic for game state, sockets, and multiplayer synchronization.

#### Tech Stack

React, TypeScript, [boardgame.io](http://boardgame.io), Zustand, and Node.js

---

## Creative Work

### Composer & Sound Designer — Film, TV & Interactive Media (2012 – Present)

[Demo Reel](https://www.youtube.com/watch?v=R1Jxx5ncKw8) | [Selected Works](https://soundcloud.com/franco-donadio/sets/selected-tracks)

14+ years as professional music composer, sound designer, and jazz performer. Collaborating with directors and creative teams on narrative identity, emotional arcs, and worldbuilding through sound. Grounded in improvisation, electroacoustic experimentation, and jazz.

**Games & Interactive Experiences — Neoquest GmbH (Zürich, Switzerland):** Original scores for three AR-enhanced outdoor escape room experiences:
- *The Thought Thief* — fantasy/mystery fairground narrative for families. [Watch](https://vimeo.com/796734203)
- *Inside – Spectrum of Gold* — AR spy thriller across three episodes: corruption, political intrigue, a bank robbery in Zurich. [Score](https://soundcloud.com/franco-donadio/brasses-strings-high-complexity?in=franco-donadio/sets/selected-tracks)
- *Adventures of the Christmas Market – The Darkest Hour* — mystery narrative set in a cursed Christmas market; music listed as a featured product element by the studio. [Score](https://soundcloud.com/franco-donadio/christmas-in-zurich-town?in=franco-donadio/sets/selected-tracks)

### Indie Rock Soloist Project (2022 – Present)

[Spotify](https://open.spotify.com/intl-es/artist/0D6RxeqImnZDpTTOVb3foH) | [Linktree](https://linktr.ee/franichicle)

---

## Education & Development

### Music Composition & Sound Design
**2012 – Present**

Professional training in composition, improvisation (jazz, soul, R&B, indie-rock), orchestration, and sound design.

The discipline of mastering music — decomposing complex systems into learnable parts, practicing with patience across years, and building intuitive real-time decision-making — directly shaped my engineering approach.

Skills/Tools:
- Ensemble writing
- Improvisation
- Ableton
- Pro Tools
- Synthesizers
- Max/MSP (visual programming environment for music, audio, and interactive media)

### Professional Jazz Musician
**2016 – Present**

The path to becoming a professional jazz player developed skills that directly transfer to engineering:

- Simplifying extremely complex material with patience across years — working a single skill set for 3 years before moving to the next
- Hearing others, relaxing and reacting only when necessary
- Knowing what to play as well as what not to play
- Decomposing difficult material into simple, small parts and learning in order with patience
- Building a second nature for improvisation — a fast, intuitive skill that shows up in real-time performance

### Self-Directed Software Engineering
**2014 – Present**

Structured self-learning path focused on software engineering fundamentals, front-end architecture, clean code principles, design patterns, and systems thinking.

  - Mentored by senior engineers at Publicis, Quadion, and FIS
  - Currently studying: AI Engineering, Model Context Protocol (MCP), Agentic Architectures

### Formal Studies

- **CSMMF (Conservatorio Superior de Música Manuel de Falla)** — Tecnicatura Superior en Jazz, 2017–2020. Earlier attendance 2007–2009 (ear training, instrument)
- **UNA (Universidad Nacional de las Artes)** — Licenciatura en Artes Musicales, Composition, 2015 (selective coursework)
- **EMC (Escuela de Música Contemporánea)** — Arrangements, Harmony & Composition, 2014

- **UBA (Universidad de Buenos Aires)** — Licenciatura en Artes, 2008–2012 (not completed). Art Theory & History (2 years), Philosophy (1 year)
- **Tecson** — Recording & Post-Production, 2005–2007 (completed)

### Private Study & Workshops

- Arrangements & Composition — Richard Nant
- Jazz Guitar — Pablo Bobrowicky, Lucio Balduini, Marcelo Gutfraind, Juan Pablo "El Colo" Arredondo
- Electroacoustic & Music Technology — Agustin Genoud (2010, Max/MSP)
- Film Scoring — Underground, Prof. Gabriel Barredo (2017)
- Jazz ensembles — Enrique Norris, Sebastián Groshaus, Sebastián Stecher
- Workshops: Barry Harris, Ralph Alessi, Andrew D'Angelo

---

## Skills

### Front-End
Development of scalable UI architecture, modular component systems, complex state flows and interactive data-driven interfaces.
Level: ***** (5/5)
Keywords: Component Design, Modular Design, Front-End Architecture, UI Patterns, SPA, State Management

### UI/UX
Design of intuitive, aesthetic and functional interfaces. Strong focus on clarity, interactivity, user flow and visual structure
Level: ***·· (3/5)
Keywords: UI/UX, Interaction Design, Usability

### Backend
API development, business logic, middleware, layered architectures and server logic, Server-side logic, backend services, domain modeling.
Level: ***·· (3/5)
Keywords: C#, WebAPI, Middleware, LINQ, .NET, .NET Core, Entity Framework, ORMs, SQL Server

### AI Engineering
MCP Servers, RAG pipelines, LLM integration, prompt engineering, agentic architectures, Spec-Driven Development, Claude Code, AI Tools
Level: ***·· (3/5)

### Testing
Unit testing for front-end and backend, test strategy design
Level: **··· (2/5)
Keywords: Unit Tests, TDD, Vitest, Jest, NUnit

### Soft Skills
Clear communicator with strong technical articulation. Cross-disciplinary thinking. High creative capacity combined with engineering rigor. Strong ownership, discipline and initiative.
Level: ***** (5/5)

### Front-End Tech-Stack
Level: ****· (4/5)
Keywords: JavaScript, TypeScript, React, Redux, Zustand, Angular, RxJS, Vite, Webpack, Vitest, Jest, Testing Library, boardgame.io, etc

### Backend Tech-Stack
Level: **··· (2/5)
Keywords: .NET, .NET Core, C#, Python WebAPI, Entity Framework, EF Core, NHibernate, OWIN, Node.js, REST APIs, Microsoft SQL Server, SQL/T-SQL, NUnit

### Creative Stack
Level: ***** (5/5)
Keywords: Film & Games Scoring, Improvisation, Sound design for interactive experiences, Art Direction, Game Systems

---

## Languages

- **English:** Fluent
- **Spanish:** Native

---

## Profiles

- [LinkedIn](https://www.linkedin.com/in/francodonadio)
- [GitHub](https://github.com/Frankietime) (@Frankietime)
- [Selected Works — SoundCloud](https://soundcloud.com/franco-donadio/sets/selected-tracks)
- [Demo Reel](https://www.youtube.com/watch?v=R1Jxx5ncKw8)
