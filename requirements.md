# Prism - Requirements Document

> **"See every facet of your codebase"**  
> AI-powered Developer Onboarding & Knowledge Management Platform  
> Submitted for: AI for Bharat by Amazon

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Objectives](#3-objectives)
4. [Stakeholders](#4-stakeholders)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [User Stories](#7-user-stories)
8. [System Requirements](#8-system-requirements)
9. [Integration Requirements](#9-integration-requirements)
10. [Data Requirements](#10-data-requirements)
11. [Security Requirements](#11-security-requirements)
12. [Constraints & Assumptions](#12-constraints--assumptions)
13. [Success Metrics](#13-success-metrics)
14. [Out of Scope](#14-out-of-scope)
15. [Glossary](#15-glossary)

---

## 1. Project Overview

### 1.1 Product Name
**Prism** — just as a prism breaks complex light into a clear, visible spectrum, Prism breaks down complex codebases into clear, connected, and understandable knowledge — making the invisible visible for every developer on the team.

### 1.2 Tagline
*"See every facet of your codebase"*

### 1.3 Product Description
Prism is an AI-powered developer onboarding and knowledge management platform that automatically builds a living knowledge graph from a team's codebase, documentation, and team conversations. It uses this graph to create personalized onboarding paths for new developers and provide instant, contextual answers to technical questions — acting as an always-available AI mentor for every developer on the team.

### 1.4 Competition Context
**Competition:** AI for Bharat by Amazon  
**Problem Statement:** Build an AI-powered solution that helps people learn faster, work smarter, or become more productive while building or understanding technology.

### 1.5 Alignment with Problem Statement

| Criteria | How Prism Addresses It |
|----------|----------------------|
| Learn faster | Personalized onboarding paths reduce ramp-up from weeks to days |
| Work smarter | Instant knowledge access eliminates time wasted hunting for information |
| More productive | Automated setup + guided learning = faster time to first contribution |
| Building technology | Developer-focused, code-native intelligence |
| Understanding technology | Knowledge graph maps how every part of the codebase connects |

---

## 2. Problem Statement

### 2.1 Core Problem
When a new developer joins a software team, they face a massive knowledge gap. Understanding "how does this code work?" requires weeks of reading outdated documentation, interrupting senior developers, and reverse-engineering logic from code — all of which is unproductive and expensive.

### 2.2 Pain Points

#### For New Developers
- Spend 2–4 weeks just figuring out how the codebase works
- Documentation is outdated, scattered, or missing entirely
- No personalized guide to what they need to learn for their specific role
- Afraid to ask "basic" questions repeatedly
- Environment setup takes days due to undocumented processes
- No way to know who the subject matter expert is for a given component

#### For Senior Developers
- Spend 20% of their time answering the same questions repeatedly
- Interrupted during deep work for onboarding-related queries
- When they leave, critical tribal knowledge is lost forever
- No visibility into what knowledge gaps exist across the team

#### For Team Admins / Tech Leads
- No standardized onboarding process across team members
- Cannot measure how long onboarding takes or where people get stuck
- No tool to identify what documentation is missing
- Manual access provisioning wastes time

### 2.3 Current Solutions & Their Gaps

| Existing Tool | Gap |
|--------------|-----|
| Confluence / Notion | Static docs, manually maintained, no code understanding |
| GitHub native search | Only searches text, no concept relationships, no learning paths |
| GitHub Copilot | Writes new code, does not explain existing codebase |
| Glean / Guru | Generic enterprise search, not developer-specific, expensive |
| Fireflies / Otter.ai | Meeting transcription only, no code or doc understanding |
| ReadMe / GitBook | Manual documentation, no AI, no auto-updating |

### 2.4 The Gap Prism Fills
There is no solution that **understands code structure natively**, **connects code to documentation to people to discussions**, and **creates personalized learning journeys** — all in one AI-powered platform.

---

## 3. Objectives

### 3.1 Primary Objectives
- **OBJ-01:** Reduce developer onboarding time from 3–4 weeks to 3–5 days
- **OBJ-02:** Provide instant, contextual answers to codebase questions using AI
- **OBJ-03:** Automatically build and maintain a living knowledge graph from code, docs, and conversations
- **OBJ-04:** Generate personalized learning paths based on developer role and experience level

### 3.2 Secondary Objectives
- **OBJ-05:** Identify and surface team knowledge gaps proactively
- **OBJ-06:** Preserve institutional/tribal knowledge automatically as code evolves
- **OBJ-07:** Reduce repeated interruptions to senior developers by 80%
- **OBJ-08:** Provide measurable onboarding analytics for team admins

---

## 4. Stakeholders

### 4.1 Primary Users

| User Type | Role | Key Needs |
|-----------|------|-----------|
| New Developer | Junior/Mid-level joining team | Personalized learning path, quick answers, guided setup |
| Senior Developer | Experienced team member | Less interruptions, easy knowledge sharing |
| Team Admin / Tech Lead | Manager overseeing onboarding | Progress visibility, analytics, gap detection |

### 4.2 Secondary Stakeholders

| Stakeholder | Interest |
|-------------|----------|
| HR / People Team | Faster, smoother onboarding experience |
| CTO / Engineering Head | Reduced cost per hire, team productivity metrics |
| Product Team | Understanding codebase for feature planning |

---

## 5. Functional Requirements

### 5.1 Knowledge Graph Engine

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-KG-01 | System must automatically ingest connected GitHub/GitLab repositories | High |
| FR-KG-02 | System must parse code using AST (Abstract Syntax Tree) to extract functions, classes, and dependencies | High |
| FR-KG-03 | System must ingest documentation from Confluence, Notion, and Markdown files | High |
| FR-KG-04 | System must mine team conversations from connected Slack workspaces | Medium |
| FR-KG-05 | System must build a graph of entities: code components, people, documents, and concepts | High |
| FR-KG-06 | System must map relationships between entities (depends-on, authored-by, documented-by, related-to) | High |
| FR-KG-07 | System must track temporal data — marking information as current or deprecated | High |
| FR-KG-08 | System must automatically update the knowledge graph when new code is pushed | Medium |
| FR-KG-09 | System must assign confidence scores to extracted relationships | Medium |
| FR-KG-10 | System must detect deprecated code and flag it with migration paths | Medium |
| FR-KG-11 | System must support multi-language codebases (Python, JavaScript, Java, Go, etc.) | Medium |
| FR-KG-12 | System must generate and store vector embeddings for all ingested content | High |

### 5.2 Intelligent Onboarding

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-OB-01 | System must allow admin to create a new team member profile (name, role, experience level) | High |
| FR-OB-02 | System must automatically generate a personalized learning path based on role and experience | High |
| FR-OB-03 | System must support multiple developer roles: Backend, Frontend, Full Stack, DevOps, Mobile | High |
| FR-OB-04 | System must support experience levels: Junior, Mid-level, Senior | High |
| FR-OB-05 | System must provide an admin interface to customize the AI-generated learning path | High |
| FR-OB-06 | System must allow toggling individual modules on or off in the learning path | Medium |
| FR-OB-07 | System must generate automated environment setup scripts for new developers | Medium |
| FR-OB-08 | System must generate a Day 1 checklist (tools to install, repos to clone, people to meet) | Medium |
| FR-OB-09 | System must track module completion progress in real-time | High |
| FR-OB-10 | System must adapt the learning path based on developer progress and questions asked | Medium |
| FR-OB-11 | System must estimate duration for each learning module | Low |
| FR-OB-12 | System must send a welcome notification to new developers with login credentials | Low |

### 5.3 AI Chat Interface

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AI-01 | System must allow developers to ask natural language questions about the codebase | High |
| FR-AI-02 | System must return answers using Retrieval Augmented Generation (RAG) from the knowledge graph | High |
| FR-AI-03 | System must include relevant code snippets with file paths and line numbers in responses | High |
| FR-AI-04 | System must cite all sources: documentation links, expert names, PR references, Slack threads | High |
| FR-AI-05 | System must identify and display subject matter experts for any given topic | Medium |
| FR-AI-06 | System must suggest related topics after answering a question | Medium |
| FR-AI-07 | System must maintain conversation history within a session | High |
| FR-AI-08 | System must allow users to provide feedback on answer quality (thumbs up/down) | Medium |
| FR-AI-09 | System must learn from feedback to improve future responses | Medium |
| FR-AI-10 | System must warn when retrieved information may be outdated or deprecated | Medium |
| FR-AI-11 | System must provide a "show more context" option for detailed answers | Low |

### 5.4 Knowledge Graph Explorer

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-EX-01 | System must provide an interactive visual graph for exploring knowledge connections | High |
| FR-EX-02 | System must allow users to click nodes to explore connected components | High |
| FR-EX-03 | System must support search by component name, person, concept, or keyword | High |
| FR-EX-04 | System must support filtering by: code, people, documentation, and discussions | Medium |
| FR-EX-05 | System must color-code node types (code = blue, people = green, docs = purple, discussions = yellow) | Medium |
| FR-EX-06 | System must show component details panel with files, experts, and related discussions | High |
| FR-EX-07 | System must display deprecation warnings on outdated components | Medium |
| FR-EX-08 | System must show a "knowledge health score" per component | Low |
| FR-EX-09 | System must provide zoom and pan controls on the graph canvas | Medium |
| FR-EX-10 | System must display "who knows about X?" expert recommendations | Medium |

### 5.5 Admin Dashboard

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AD-01 | System must display team-level metrics: total developers, active onboardings, average onboarding time, knowledge coverage | High |
| FR-AD-02 | System must display a real-time activity feed of recent onboarding events | Medium |
| FR-AD-03 | System must detect and display knowledge gaps based on frequently asked questions | High |
| FR-AD-04 | System must display a team progress table with per-developer status | High |
| FR-AD-05 | System must allow admin to manage GitHub, Slack, and documentation integrations | High |
| FR-AD-06 | System must provide a 4-step setup wizard for configuring new team members | High |
| FR-AD-07 | System must allow admin to export onboarding reports | Low |
| FR-AD-08 | System must display documentation health scores | Low |
| FR-AD-09 | System must allow admin to set access permissions per developer | Medium |

### 5.6 User Authentication & Access Control

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AU-01 | System must support user registration and login via email/password | High |
| FR-AU-02 | System must support OAuth 2.0 login via GitHub | Medium |
| FR-AU-03 | System must implement Role-Based Access Control (RBAC) with three roles: Admin, Senior Developer, New Developer | High |
| FR-AU-04 | System must restrict admin features to Admin role only | High |
| FR-AU-05 | System must issue JWT tokens for session management | High |
| FR-AU-06 | System must support session expiry and re-authentication | Medium |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PE-01 | AI chat response time | < 3 seconds for 95% of queries |
| NFR-PE-02 | Knowledge graph query time | < 1 second for standard queries |
| NFR-PE-03 | Dashboard load time | < 2 seconds |
| NFR-PE-04 | Initial knowledge graph build time | < 30 minutes for repos up to 100K lines |
| NFR-PE-05 | Incremental graph update time | < 5 minutes after a new commit |
| NFR-PE-06 | API endpoint response time | < 500ms for non-AI endpoints |

### 6.2 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SC-01 | Concurrent users supported | Minimum 100 concurrent users |
| NFR-SC-02 | Codebase size supported | Up to 1 million lines of code |
| NFR-SC-03 | Team size supported | Up to 500 developers per workspace |
| NFR-SC-04 | Repository count | Up to 50 repositories per workspace |
| NFR-SC-05 | Knowledge graph size | Up to 1 million nodes and 5 million relationships |

### 6.3 Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-RE-01 | System uptime | 99.5% availability |
| NFR-RE-02 | Data durability | Zero data loss on system restart |
| NFR-RE-03 | Graceful degradation | System must remain functional if one AI service is unavailable |
| NFR-RE-04 | Error handling | All API errors must return meaningful error messages |

### 6.4 Usability

| ID | Requirement |
|----|-------------|
| NFR-US-01 | New developer must be able to start their learning path within 10 minutes of first login |
| NFR-US-02 | Admin must be able to onboard a new team member within 5 minutes |
| NFR-US-03 | AI chat interface must be usable without any training or documentation |
| NFR-US-04 | All screens must be responsive and functional on desktop browsers |
| NFR-US-05 | System must provide clear error messages with actionable next steps |

### 6.5 Security

| ID | Requirement |
|----|-------------|
| NFR-SE-01 | All data must be encrypted in transit using TLS 1.2 or higher |
| NFR-SE-02 | All sensitive data must be encrypted at rest |
| NFR-SE-03 | API keys must never be exposed in frontend code or logs |
| NFR-SE-04 | All endpoints must be protected against NoSQL injection and XSS attacks |
| NFR-SE-05 | Source code must not be sent to third-party LLM providers without explicit consent |
| NFR-SE-06 | Rate limiting must be enforced on all API endpoints |

### 6.6 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-MA-01 | Codebase must follow consistent coding standards (Black for Python, ESLint for JavaScript) |
| NFR-MA-02 | All API endpoints must be documented via auto-generated FastAPI docs |
| NFR-MA-03 | Unit test coverage must be minimum 70% for backend services |
| NFR-MA-04 | All components must be containerized using Docker |

---

## 7. User Stories

### 7.1 New Developer Stories

```
US-ND-01: Personalized Onboarding Path
As a new developer,
I want to see a personalized learning path on my first day,
So that I know exactly what to learn and in what order for my specific role.

US-ND-02: Codebase Questions
As a new developer,
I want to ask natural language questions about the codebase,
So that I can understand how things work without interrupting my teammates.

US-ND-03: Progress Tracking
As a new developer,
I want to track my onboarding progress,
So that I know how far along I am and what's remaining.

US-ND-04: Expert Discovery
As a new developer,
I want to know who the expert is for any given component,
So that I can reach out to the right person when I need deeper help.

US-ND-05: Environment Setup
As a new developer,
I want an automated setup script for my development environment,
So that I can be up and running on Day 1 without manual troubleshooting.

US-ND-06: Knowledge Graph Exploration
As a new developer,
I want to visually explore how different parts of the codebase connect,
So that I can build a mental model of the system quickly.
```

### 7.2 Senior Developer Stories

```
US-SD-01: Reduce Interruptions
As a senior developer,
I want AI to answer common questions automatically,
So that I can focus on deep work without constant interruptions.

US-SD-02: Knowledge Contribution
As a senior developer,
I want to see what questions are being asked about my code,
So that I can proactively improve documentation for confusing areas.

US-SD-03: Mentoring Support
As a senior developer,
I want to review new developer progress,
So that I can offer targeted help when they are genuinely stuck.

US-SD-04: Documentation Suggestions
As a senior developer,
I want the system to suggest what documentation is missing,
So that I can fill knowledge gaps before they cause problems.
```

### 7.3 Admin Stories

```
US-AD-01: New Member Setup
As a team admin,
I want to add a new team member and configure their onboarding in under 5 minutes,
So that their first day experience is smooth and structured.

US-AD-02: Progress Monitoring
As a team admin,
I want a dashboard showing each developer's onboarding progress,
So that I can identify who is behind and intervene early.

US-AD-03: Knowledge Gap Detection
As a team admin,
I want the system to automatically identify frequently asked questions with poor documentation,
So that I can prioritize documentation improvements.

US-AD-04: Integration Management
As a team admin,
I want to connect GitHub, Slack, and documentation tools in a few clicks,
So that the knowledge graph builds automatically without manual data entry.

US-AD-05: Analytics & Reporting
As a team admin,
I want to see metrics like average onboarding time and time to first commit,
So that I can measure and improve the onboarding process over time.
```

---

## 8. System Requirements

### 8.1 Development Environment

| Component | Requirement |
|-----------|-------------|
| Python | 3.11 or higher |
| Node.js | 18.0 or higher |
| Docker | 24.0 or higher |
| Docker Compose | 2.20 or higher |
| Git | 2.40 or higher |
| Neo4j | 5.0 or higher |
| MongoDB | 6.0 or higher |
| Redis | 7.0 or higher |

### 8.2 Hardware Requirements (Development)

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 20 GB free | 50 GB free |
| Network | Stable internet for API calls | Broadband |

### 8.3 Production Environment

| Component | Specification |
|-----------|--------------|
| Frontend Hosting | Vercel (CDN-backed) |
| Backend Hosting | Render or Railway (minimum 1 GB RAM) |
| Graph Database | Neo4j Aura (cloud-managed) |
| Document Database | MongoDB Atlas (free tier - 512MB) |
| Vector Database | ChromaDB (self-hosted) or Pinecone |
| Cache | Upstash Redis |
| Container Orchestration | Docker Compose (development), single-server deployment (MVP) |

---

## 9. Integration Requirements

### 9.1 Required Integrations (MVP)

| Integration | Purpose | Auth Method |
|-------------|---------|-------------|
| GitHub API | Fetch repos, PRs, issues, commit history, file contents | OAuth App / Personal Access Token |
| OpenAI GPT-4 API | Language model for understanding and generating answers | API Key |
| Slack API | Mine team conversations and discussions | OAuth 2.0 Bot Token |

### 9.2 Optional Integrations (Post-MVP)

| Integration | Purpose |
|-------------|---------|
| GitLab API | Alternative to GitHub for teams using GitLab |
| Confluence API | Ingest enterprise documentation |
| Notion API | Ingest team wikis and documentation |
| Jira / Linear | Link code components to tickets and issues |
| Google Drive | Ingest design docs and meeting notes |

### 9.3 Integration Requirements

| ID | Requirement |
|----|-------------|
| IR-01 | All integrations must use official APIs with proper OAuth or token-based authentication |
| IR-02 | Integration credentials must be stored encrypted and never exposed in logs |
| IR-03 | System must gracefully handle API rate limits with exponential backoff |
| IR-04 | Integration failures must not crash the main application |
| IR-05 | System must provide clear status indicators for each connected integration |
| IR-06 | Admin must be able to revoke any integration at any time |

---

## 10. Data Requirements

### 10.1 Data Sources

| Source | Data Extracted | Update Frequency |
|--------|---------------|-----------------|
| GitHub Repositories | Code files, functions, classes, dependencies, PRs, issues | On every push (webhook) |
| Slack Workspace | Messages, threads, decisions, problem-solution pairs | Every 6 hours |
| Documentation (Confluence/Notion/MD) | Articles, guides, architecture docs | Daily sync |
| Git History | Commit messages, authorship, file change history | On every push |

### 10.2 Data Storage Requirements

| Data Type | Storage System | Reason |
|-----------|---------------|--------|
| Knowledge graph entities & relationships | Neo4j | Purpose-built graph database |
| Vector embeddings for semantic search | ChromaDB | Optimized for similarity search |
| User profiles, progress, configurations | MongoDB | Flexible document storage, schema-less design ideal for variable learning path structures |
| API responses, session data | Redis | Fast in-memory cache |

### 10.3 Data Retention

| Data Type | Retention Period |
|-----------|-----------------|
| User activity logs | 90 days |
| Onboarding progress data | Indefinite (user account lifetime) |
| Knowledge graph data | Indefinite (updated continuously) |
| Chat history | 30 days (or until user deletes) |
| Cached API responses | 24 hours |

### 10.4 Data Privacy Requirements

| ID | Requirement |
|----|-------------|
| DP-01 | Source code must be processed locally and not stored in third-party systems without explicit consent |
| DP-02 | Only anonymized usage metrics may be used for system improvement |
| DP-03 | Users must be able to request deletion of their personal data |
| DP-04 | Personally identifiable information (PII) must never be logged |

---

## 11. Security Requirements

### 11.1 Authentication & Authorization

| ID | Requirement |
|----|-------------|
| SEC-01 | All API endpoints must require valid JWT authentication tokens |
| SEC-02 | JWT tokens must expire after 24 hours |
| SEC-03 | Refresh tokens must be stored securely (HttpOnly cookies) |
| SEC-04 | Role-based access control must be enforced at the API layer |
| SEC-05 | Admin endpoints must require additional verification |

### 11.2 Data Security

| ID | Requirement |
|----|-------------|
| SEC-06 | All API keys and secrets must be stored as environment variables, never hardcoded |
| SEC-07 | Database connections must use TLS |
| SEC-08 | Sensitive configuration must be managed via a secrets manager in production |
| SEC-09 | All file uploads must be scanned for malicious content |

### 11.3 API Security

| ID | Requirement |
|----|-------------|
| SEC-10 | Rate limiting: 100 requests/minute per user for standard endpoints |
| SEC-11 | Rate limiting: 20 requests/minute per user for AI chat endpoints |
| SEC-12 | All inputs must be validated and sanitized before processing |
| SEC-13 | CORS must be configured to allow only trusted origins |
| SEC-14 | HTTP security headers must be set (HSTS, X-Frame-Options, CSP) |

---

## 12. Constraints & Assumptions

### 12.1 Constraints

| ID | Constraint |
|----|------------|
| CON-01 | MVP must be buildable within 3 weeks with a small team |
| CON-02 | Initial budget for API credits: ₹5,000–₹10,000 |
| CON-03 | Must use free tiers of hosting services for MVP deployment |
| CON-04 | Must support at minimum: Python, JavaScript, and one other language in code analysis |
| CON-05 | System must function without requiring changes to the team's existing code repositories |
| CON-06 | Mobile app is out of scope for MVP |

### 12.2 Assumptions

| ID | Assumption |
|----|------------|
| ASM-01 | Target teams use GitHub or GitLab for version control |
| ASM-02 | Target teams use Slack for team communication |
| ASM-03 | Teams have at least basic documentation (README files) in their repositories |
| ASM-04 | Admin users have the authority to grant third-party API access to tools like GitHub and Slack |
| ASM-05 | Developers have access to a modern web browser (Chrome, Firefox, Edge, Safari) |
| ASM-06 | OpenAI GPT-4 API remains available and cost-effective for MVP usage levels |
| ASM-07 | Team size is between 5–100 developers for MVP target market |

---

## 13. Success Metrics

### 13.1 Primary KPIs

| Metric | Baseline (Without Prism) | Target (With Prism) |
|--------|--------------------------|---------------------|
| Onboarding time | 3–4 weeks | 3–5 days |
| Time to first commit | 10–14 days | 3–5 days |
| Repeated questions per week | 50+ per team | Under 10 per team |
| Documentation freshness | Manual, often outdated | Auto-updated continuously |
| Senior dev time on onboarding | ~20% of working hours | Under 5% of working hours |

### 13.2 Product Metrics

| Metric | Target |
|--------|--------|
| AI answer accuracy (thumbs up rate) | > 80% |
| Knowledge graph coverage | > 70% of codebase components documented |
| Daily active usage by onboarding devs | > 80% |
| Onboarding completion rate | > 90% within expected timeline |
| Setup time for admin to add new member | Under 5 minutes |

### 13.3 Technical Metrics

| Metric | Target |
|--------|--------|
| AI response time | < 3 seconds (P95) |
| System uptime | > 99.5% |
| Knowledge graph build time | < 30 minutes for first build |
| Incremental update time | < 5 minutes after code push |

---

## 14. Out of Scope

The following features are explicitly **not** included in the MVP:

| Feature | Reason |
|---------|--------|
| Mobile application (iOS/Android) | Deferred to post-MVP |
| Slack bot for answering questions within Slack | Post-MVP integration |
| Video-based learning modules | Out of core scope |
| AI-generated code documentation | Future feature |
| Integration with Jira / Linear | Post-MVP |
| Multi-language UI (non-English) | Post-MVP |
| Real-time collaborative editing of learning paths | Post-MVP |
| Performance reviews or HR analytics | Out of scope entirely |
| Automated PR reviews | Different product category |
| Enterprise SSO (SAML/LDAP) | Post-MVP |

---

## 15. Glossary

| Term | Definition |
|------|------------|
| **Prism** | The product name. Just as a prism refracts light into a clear spectrum, Prism refracts complex codebases into clear, connected, understandable knowledge for every developer |
| **Knowledge Graph** | A structured representation of entities (code, people, documents) and their relationships, stored in a graph database |
| **Vertex/Node** | A single entity in the knowledge graph (e.g., a code component, a person, a document) |
| **Edge/Relationship** | A connection between two nodes in the knowledge graph (e.g., "depends-on", "authored-by") |
| **RAG** | Retrieval Augmented Generation — a technique where an AI model retrieves relevant context from a database before generating a response |
| **AST** | Abstract Syntax Tree — a parsed representation of source code that reveals its structure and components |
| **LangChain** | An AI orchestration framework used to build chains of operations involving language models |
| **Onboarding Path** | A personalized sequence of learning modules generated for a new developer based on their role and experience |
| **Tribal Knowledge** | Institutional knowledge that exists only in people's heads and is not documented anywhere |
| **Embeddings** | Numerical vector representations of text that enable semantic similarity search |
| **Neo4j** | The graph database used by Prism to store the knowledge graph |
| **MongoDB** | The document database used by Prism to store user profiles, onboarding progress, learning paths, and analytics data — chosen for its flexible, JSON-like document structure that maps naturally to variable learning path configurations |
| **MongoDB Atlas** | Cloud-hosted managed MongoDB service used for production deployment (free tier: 512MB) |
| **PyMongo / Motor** | Python libraries used to interact with MongoDB — Motor is the async version, ideal for FastAPI |
| **Beanie** | MongoDB ODM (Object Document Mapper) for FastAPI — similar to SQLAlchemy but for MongoDB documents |
| **ChromaDB** | The vector database used by Prism to store and search text embeddings |
| **RBAC** | Role-Based Access Control — a security model that restricts feature access based on the user's assigned role |
| **MVP** | Minimum Viable Product — the initial version of Prism built for the hackathon |
| **JWT** | JSON Web Token — a secure token format used for user authentication |
| **API** | Application Programming Interface — a set of endpoints through which different software components communicate |

---

*Document Version: 1.1 (Updated: MongoDB replaces PostgreSQL)*  
*Last Updated: February 2026*  
*Project: Prism — AI for Bharat by Amazon*  
*Status: Draft for Hackathon Submission*