# Prism - Design Document

> **"See every facet of your codebase"**  
> AI-powered Developer Onboarding & Knowledge Management Platform  
> Submitted for: AI for Bharat by Amazon

---

## Table of Contents

1. [Design Overview](#1-design-overview)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Database Design](#4-database-design)
5. [API Design](#5-api-design)
6. [AI & Agent Design](#6-ai--agent-design)
7. [Data Flow Design](#7-data-flow-design)
8. [UI/UX Design](#8-uiux-design)
9. [Security Design](#9-security-design)
10. [Deployment Design](#10-deployment-design)
11. [Tech Stack Summary](#11-tech-stack-summary)
12. [Design Decisions & Rationale](#12-design-decisions--rationale)

---

## 1. Design Overview

### 1.1 Purpose of This Document
This document describes the technical design and architecture of **Prism** — how it is built, how its components interact, and why specific design decisions were made. It serves as the implementation blueprint for the development team.

### 1.2 Design Philosophy

| Principle | How Prism Applies It |
|-----------|---------------------|
| **AI-First** | Every feature is designed around AI capabilities, not added as an afterthought |
| **Code-Native** | Understands code structure deeply using AST, not just text search |
| **Developer Experience** | Simple, fast, intuitive — developers should love using it |
| **Modularity** | Each component is independently deployable and replaceable |
| **Scalability** | Designed to grow from 10 to 500+ developers without redesign |

### 1.3 High-Level System Summary

```
Users (Web App)
    ↓ Natural language questions / onboarding interactions
FastAPI Gateway
    ↓ Authenticated requests
AI Agent Layer (LangChain + GPT-4)
    ↓ Retrieval queries / graph traversal
Data Layer (Neo4j + ChromaDB + MongoDB + Redis)
    ↑ Continuous sync
Ingestion Layer (Code Parser + Doc Processor + NLP Miner)
    ↑ Webhooks + scheduled jobs
External Sources (GitHub + Slack + Confluence/Notion)
```

---

## 2. System Architecture

### 2.1 Architecture Overview

Prism uses a **layered microservice-inspired architecture** with 6 distinct layers, each with a clear responsibility:

```
┌─────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                       │
│         React Web App | Mobile (Future) | Slack Bot     │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTPS / WebSocket
┌─────────────────────────▼───────────────────────────────┐
│                  API GATEWAY LAYER                       │
│              FastAPI + JWT Auth + Rate Limiting          │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│               AI PROCESSING LAYER                        │
│   LangChain Agent | RAG Engine | Personalization Engine  │
│              GPT-4 API Interface                         │
└────────┬──────────────┬──────────────┬──────────────────┘
         │              │              │
┌────────▼──────┐ ┌─────▼──────┐ ┌───▼────────────────────┐
│  Neo4j        │ │ ChromaDB   │ │ MongoDB + Redis         │
│  Knowledge    │ │ Vector     │ │ (User Data + Cache)     │
│  Graph        │ │ Store      │ │                         │
└───────────────┘ └────────────┘ └────────────────────────┘
         ▲              ▲
┌────────┴──────────────┴─────────────────────────────────┐
│               INGESTION & PROCESSING LAYER               │
│   Code Analyzer | Doc Processor | Communication Miner    │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│               EXTERNAL DATA SOURCES                      │
│         GitHub API | Slack API | Confluence/Notion       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Patterns Used

| Pattern | Where Applied | Why |
|---------|--------------|-----|
| **RAG (Retrieval Augmented Generation)** | AI Chat | Grounds GPT-4 responses in actual codebase data |
| **Event-Driven Updates** | Knowledge Graph | Webhooks trigger graph updates on code push |
| **Repository Pattern** | Data Layer | Abstracts MongoDB/Neo4j access from business logic |
| **Dependency Injection** | FastAPI | Clean testable service architecture |
| **CQRS (simplified)** | API Layer | Separates read (graph queries) from write (ingestion) |

---

## 3. Component Design

### 3.1 Knowledge Graph Engine

**Purpose:** Build and continuously maintain a living graph of all knowledge in the team's tech ecosystem.

**Technology:** Neo4j (graph storage) + Tree-sitter (code parsing) + spaCy (NLP)

**Responsibilities:**
- Parse code repositories into structured entities
- Extract relationships between entities
- Process documentation and map to code entities
- Mine conversations for technical knowledge
- Track what is current vs deprecated

**Key Classes:**

```python
class KnowledgeGraphEngine:
    """
    Core engine for building and querying the knowledge graph
    """
    def __init__(self, neo4j_driver, embedding_model):
        self.driver = neo4j_driver
        self.embedder = embedding_model

    def ingest_repository(self, repo_url: str) -> IngestResult:
        """Parse entire GitHub repo and build graph"""

    def update_from_commit(self, commit_sha: str) -> UpdateResult:
        """Incremental update on new code push"""

    def query_component(self, component_name: str) -> ComponentDetails:
        """Get full details about a code component"""

    def find_experts(self, topic: str) -> List[Expert]:
        """Find who knows most about a given topic"""

    def detect_knowledge_gaps(self) -> List[KnowledgeGap]:
        """Identify underdocumented components"""
```

**Node Types in Graph:**

```
CodeComponent
├── Properties: id, name, type, language, file_path,
│              line_start, line_end, complexity, is_deprecated
└── Types: function, class, module, API endpoint, schema

Person
├── Properties: id, name, email, role, slack_id, github_username
└── Derived: expertise_score (from contributions)

Document
├── Properties: id, title, url, source, last_updated, content_hash
└── Types: readme, architecture_doc, API_doc, slack_thread, PR_description

Concept
├── Properties: id, name, description, tags
└── Examples: "authentication", "payment flow", "retry logic"
```

**Relationship Types:**

```
DEPENDS_ON      → CodeComponent depends on another CodeComponent
IMPLEMENTS      → CodeComponent implements a Concept
DOCUMENTED_BY   → CodeComponent is explained in a Document
AUTHORED_BY     → CodeComponent was written by a Person
RELATED_TO      → Concept is related to another Concept
DISCUSSED_IN    → Concept was discussed in a Document (Slack/PR)
DEPRECATED_BY   → Old CodeComponent replaced by new one
EXPERT_IN       → Person has expertise in a Concept
```

---

### 3.2 Ingestion Service

**Purpose:** Connect to external data sources and feed structured data into the knowledge graph.

**Technology:** GitHub API + Slack API + GitPython + Tree-sitter + spaCy

**Sub-components:**

#### 3.2.1 Code Analyzer
```python
class CodeAnalyzer:
    """
    Parses source code using AST to extract
    structured entities and relationships
    """
    supported_languages = [
        "python", "javascript", "typescript",
        "java", "go", "rust", "ruby"
    ]

    def parse_file(self, file_path: str, language: str) -> List[Entity]:
        """Extract functions, classes, imports from a file"""

    def extract_dependencies(self, file_path: str) -> List[Dependency]:
        """Map what this file imports and calls"""

    def analyze_complexity(self, function_node) -> int:
        """Calculate cyclomatic complexity"""
```

#### 3.2.2 Document Processor
```python
class DocumentProcessor:
    """
    Ingests documentation and generates
    embeddings for semantic search
    """
    def process_markdown(self, content: str) -> ProcessedDoc:
        """Parse README, wikis, and markdown docs"""

    def process_confluence_page(self, page_id: str) -> ProcessedDoc:
        """Fetch and process Confluence pages"""

    def generate_embeddings(self, text: str) -> List[float]:
        """Generate vector embeddings using Sentence Transformers"""

    def chunk_document(self, text: str, chunk_size=512) -> List[str]:
        """Split large docs into searchable chunks"""
```

#### 3.2.3 Communication Miner
```python
class CommunicationMiner:
    """
    Extracts technical knowledge from team
    Slack conversations and GitHub discussions
    """
    def mine_slack_channel(self, channel_id: str) -> List[Discussion]:
        """Extract technical Q&A and decisions from Slack"""

    def extract_decisions(self, messages: List[Message]) -> List[Decision]:
        """Identify architectural decisions in conversations"""

    def link_to_code(self, discussion: Discussion) -> List[CodeComponent]:
        """Connect discussions to relevant code entities"""
```

---

### 3.3 AI Agent Service

**Purpose:** Orchestrate AI workflows — understanding questions, retrieving context, generating answers.

**Technology:** LangChain + OpenAI GPT-4 + Sentence Transformers

**Architecture:**

```python
class PrismAIAgent:
    """
    Main AI agent powered by LangChain
    Handles all natural language interactions
    """
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.graph_tool = KnowledgeGraphTool()
        self.vector_tool = VectorSearchTool()
        self.memory = ConversationBufferMemory()

    def answer_question(
        self,
        question: str,
        user_context: UserContext
    ) -> AIResponse:
        """
        Full RAG pipeline:
        1. Understand question intent
        2. Retrieve relevant graph nodes
        3. Semantic search for similar content
        4. Generate grounded answer with citations
        """

    def generate_learning_path(
        self,
        role: str,
        experience: str,
        repos: List[str]
    ) -> LearningPath:
        """Generate personalized onboarding roadmap"""

    def detect_knowledge_gaps(
        self,
        chat_history: List[Message]
    ) -> List[KnowledgeGap]:
        """Analyze questions to find documentation gaps"""
```

**LangChain Tools Available to Agent:**

```python
tools = [
    Tool(
        name="GraphSearch",
        description="Search the knowledge graph for code components, people, and relationships",
        func=graph_search_tool
    ),
    Tool(
        name="SemanticSearch",
        description="Find semantically similar documentation and discussions",
        func=semantic_search_tool
    ),
    Tool(
        name="ExpertFinder",
        description="Find who knows most about a given component or concept",
        func=expert_finder_tool
    ),
    Tool(
        name="CodeExplainer",
        description="Retrieve and explain specific code files or functions",
        func=code_explainer_tool
    ),
    Tool(
        name="DeprecationChecker",
        description="Check if a component is deprecated and find its replacement",
        func=deprecation_checker_tool
    )
]
```

---

### 3.4 Personalization Engine

**Purpose:** Generate and adapt learning paths based on developer role, experience, and progress.

**Technology:** Python + LangChain + MongoDB

```python
class PersonalizationEngine:
    """
    Generates role-based personalized learning paths
    and adapts them based on progress
    """

    ROLE_TEMPLATES = {
        "backend": ["env_setup", "architecture", "database_layer",
                   "api_design", "auth_system", "testing", "deployment"],
        "frontend": ["env_setup", "architecture", "ui_components",
                    "state_management", "api_integration", "testing"],
        "devops":   ["env_setup", "infrastructure", "ci_cd",
                    "monitoring", "deployment", "security"],
        "fullstack": ["env_setup", "architecture", "backend_core",
                     "frontend_core", "integration", "deployment"]
    }

    def generate_path(
        self,
        role: str,
        experience: str,
        repos: List[Repository]
    ) -> LearningPath:
        """
        Uses role template + AI analysis of actual repo
        to generate a custom path
        """

    def adapt_path(
        self,
        user_id: str,
        progress: Progress,
        questions_asked: List[str]
    ) -> LearningPath:
        """
        Adjusts path based on:
        - Modules completed faster than expected (skip ahead)
        - Topics frequently questioned (add more depth)
        - Consistently stuck modules (add supplementary resources)
        """

    def estimate_duration(
        self,
        module: Module,
        experience: str
    ) -> int:
        """Returns estimated hours based on complexity and experience"""
```

---

### 3.5 Authentication Service

**Purpose:** Handle user registration, login, JWT issuance, and role-based access control.

**Technology:** FastAPI + Python-Jose (JWT) + Passlib (password hashing) + MongoDB

```python
class AuthService:
    def register_user(self, user_data: UserCreate) -> User:
        """Hash password, create user in MongoDB"""

    def login(self, email: str, password: str) -> TokenPair:
        """Verify credentials, return access + refresh tokens"""

    def verify_token(self, token: str) -> TokenPayload:
        """Validate JWT and extract user info"""

    def refresh_token(self, refresh_token: str) -> TokenPair:
        """Issue new access token using refresh token"""

    def get_current_user(self, token: str) -> User:
        """Dependency injection helper for FastAPI routes"""
```

**JWT Token Structure:**
```json
{
  "sub": "user_id_here",
  "email": "rahul@company.com",
  "role": "new_developer",
  "workspace_id": "workspace_id_here",
  "exp": 1735689600,
  "iat": 1735603200
}
```

---

## 4. Database Design

### 4.1 Neo4j — Knowledge Graph

**Purpose:** Store all knowledge entities and their relationships.

**Schema:**

```cypher
// Node constraints and indexes
CREATE CONSTRAINT code_component_id
ON (c:CodeComponent) ASSERT c.id IS UNIQUE;

CREATE CONSTRAINT person_email
ON (p:Person) ASSERT p.email IS UNIQUE;

CREATE INDEX component_name
FOR (c:CodeComponent) ON (c.name);

CREATE INDEX concept_name
FOR (c:Concept) ON (c.name);

// Example: Create a code component node
CREATE (c:CodeComponent {
  id: "uuid-here",
  name: "retry_payment",
  type: "function",
  language: "python",
  file_path: "src/payments/retry_handler.py",
  line_start: 45,
  line_end: 89,
  is_deprecated: false,
  complexity: 7,
  created_at: datetime(),
  updated_at: datetime()
})

// Example: Create relationship
MATCH (c:CodeComponent {name: "retry_payment"})
MATCH (p:Person {email: "sarah@company.com"})
CREATE (c)-[:AUTHORED_BY {
  commit_count: 8,
  last_commit: datetime()
}]->(p)
```

**Key Cypher Queries:**

```cypher
-- Find everything connected to a component
MATCH (c:CodeComponent {name: $name})-[r]-(connected)
RETURN c, r, connected
LIMIT 50

-- Find experts for a topic
MATCH (p:Person)-[:EXPERT_IN]->(concept:Concept {name: $topic})
RETURN p.name, p.email, p.expertise_score
ORDER BY p.expertise_score DESC
LIMIT 5

-- Find knowledge gaps (components with no documentation)
MATCH (c:CodeComponent)
WHERE NOT (c)-[:DOCUMENTED_BY]->(:Document)
AND c.complexity > 5
RETURN c.name, c.file_path, c.complexity
ORDER BY c.complexity DESC

-- Trace dependency chain
MATCH path = (c:CodeComponent {name: $name})-[:DEPENDS_ON*1..3]->(dep)
RETURN path
```

---

### 4.2 ChromaDB — Vector Store

**Purpose:** Store vector embeddings for semantic search across all content.

**Collections:**

```python
# Collection 1: Code embeddings
code_collection = chroma_client.create_collection(
    name="code_chunks",
    metadata={"description": "Code functions and classes"}
)

# Collection 2: Documentation embeddings
docs_collection = chroma_client.create_collection(
    name="documentation",
    metadata={"description": "All documentation content"}
)

# Collection 3: Conversation embeddings
conversations_collection = chroma_client.create_collection(
    name="conversations",
    metadata={"description": "Slack threads and GitHub discussions"}
)
```

**Document Structure in ChromaDB:**
```python
code_collection.add(
    ids=["component_uuid"],
    embeddings=[embedding_vector],  # 384-dim vector
    documents=["def retry_payment(id): ..."],  # actual content
    metadatas=[{
        "type": "function",
        "file_path": "src/payments/retry_handler.py",
        "language": "python",
        "component_id": "neo4j_node_id",  # link back to graph
        "is_deprecated": False
    }]
)
```

**Semantic Search Query:**
```python
results = code_collection.query(
    query_texts=["how does payment retry work"],
    n_results=5,
    where={"is_deprecated": False}
)
```

---

### 4.3 MongoDB — Application Data

**Purpose:** Store all application data — users, workspaces, learning paths, progress, analytics.

**Collections & Schemas:**

#### Collection 1: `users`
```json
{
  "_id": "ObjectId",
  "name": "Rahul Sharma",
  "email": "rahul@company.com",
  "password_hash": "bcrypt_hash",
  "role": "new_developer",
  "workspace_id": "ObjectId",
  "github_username": "rahuldev",
  "slack_user_id": "U12345",
  "experience_level": "junior",
  "developer_role": "backend",
  "created_at": "ISODate",
  "last_login": "ISODate",
  "is_active": true
}
```

#### Collection 2: `workspaces`
```json
{
  "_id": "ObjectId",
  "name": "Acme Corp Engineering",
  "admin_id": "ObjectId",
  "members": ["ObjectId", "ObjectId"],
  "integrations": {
    "github": {
      "connected": true,
      "token_encrypted": "encrypted_token",
      "repos": ["repo1", "repo2"],
      "last_sync": "ISODate"
    },
    "slack": {
      "connected": true,
      "token_encrypted": "encrypted_token",
      "channels": ["general", "engineering"],
      "last_sync": "ISODate"
    },
    "confluence": {
      "connected": false
    }
  },
  "created_at": "ISODate"
}
```

#### Collection 3: `learning_paths`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "workspace_id": "ObjectId",
  "developer_role": "backend",
  "experience_level": "junior",
  "overall_progress": 45,
  "estimated_total_days": 10,
  "started_at": "ISODate",
  "completed_at": null,
  "modules": [
    {
      "id": "module_uuid",
      "title": "Environment Setup",
      "description": "Set up your local development environment",
      "status": "completed",
      "progress": 100,
      "estimated_hours": 4,
      "actual_hours": 3,
      "resources": [
        {
          "type": "document",
          "title": "Setup Guide",
          "url": "confluence/setup-guide",
          "source": "confluence"
        },
        {
          "type": "code",
          "title": "docker-compose.yml",
          "file_path": "docker-compose.yml"
        }
      ],
      "experts": [
        {
          "name": "Sarah Chen",
          "email": "sarah@company.com",
          "reason": "DevOps lead, authored setup scripts"
        }
      ],
      "started_at": "ISODate",
      "completed_at": "ISODate"
    },
    {
      "id": "module_uuid_2",
      "title": "Authentication System",
      "status": "in_progress",
      "progress": 60,
      "estimated_hours": 6,
      "actual_hours": 3,
      "resources": [],
      "experts": [],
      "started_at": "ISODate",
      "completed_at": null
    }
  ],
  "ai_generated": true,
  "last_adapted": "ISODate"
}
```

#### Collection 4: `chat_sessions`
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "workspace_id": "ObjectId",
  "title": "How does authentication work?",
  "messages": [
    {
      "id": "msg_uuid",
      "role": "user",
      "content": "How does the payment retry logic work?",
      "timestamp": "ISODate"
    },
    {
      "id": "msg_uuid_2",
      "role": "assistant",
      "content": "The payment retry system uses exponential backoff...",
      "sources": [
        {
          "type": "code",
          "file": "src/payments/retry_handler.py",
          "lines": "45-89"
        },
        {
          "type": "document",
          "title": "Payment Architecture Doc",
          "url": "confluence/payment-arch"
        },
        {
          "type": "expert",
          "name": "Sarah Chen",
          "email": "sarah@company.com"
        }
      ],
      "feedback": "positive",
      "timestamp": "ISODate"
    }
  ],
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### Collection 5: `analytics`
```json
{
  "_id": "ObjectId",
  "workspace_id": "ObjectId",
  "date": "ISODate",
  "metrics": {
    "total_developers": 20,
    "actively_onboarding": 3,
    "completed_onboarding": 15,
    "avg_onboarding_days": 4.2,
    "total_questions_asked": 142,
    "questions_answered_by_ai": 128,
    "ai_answer_satisfaction": 0.84
  },
  "knowledge_gaps": [
    {
      "topic": "payment retry logic",
      "question_count": 8,
      "last_asked": "ISODate",
      "has_documentation": false
    },
    {
      "topic": "auth middleware",
      "question_count": 6,
      "last_asked": "ISODate",
      "has_documentation": true
    }
  ]
}
```

**MongoDB Indexes:**
```javascript
// users collection
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "workspace_id": 1 })

// learning_paths collection
db.learning_paths.createIndex({ "user_id": 1 }, { unique: true })
db.learning_paths.createIndex({ "workspace_id": 1 })

// chat_sessions collection
db.chat_sessions.createIndex({ "user_id": 1 })
db.chat_sessions.createIndex({ "created_at": -1 })

// analytics collection
db.analytics.createIndex({ "workspace_id": 1, "date": -1 })
```

---

### 4.4 Redis — Cache

**Purpose:** Cache frequent queries and manage sessions.

**Key Patterns:**
```
prism:session:{user_id}           → JWT session data (TTL: 24h)
prism:graph:query:{hash}          → Cached graph query results (TTL: 1h)
prism:ai:response:{question_hash} → Cached AI responses (TTL: 6h)
prism:user:profile:{user_id}      → Cached user profile (TTL: 30min)
prism:workspace:stats:{ws_id}     → Cached dashboard stats (TTL: 15min)
prism:ratelimit:{user_id}         → API rate limit counter (TTL: 1min)
```

---

## 5. API Design

### 5.1 Base URL & Versioning
```
Development:  http://localhost:8000/api/v1
Production:   https://api.prism.dev/api/v1
```

### 5.2 Authentication Endpoints

```
POST   /api/v1/auth/register        Register new user
POST   /api/v1/auth/login           Login and get tokens
POST   /api/v1/auth/refresh         Refresh access token
POST   /api/v1/auth/logout          Invalidate tokens
GET    /api/v1/auth/me              Get current user profile
```

**POST /api/v1/auth/login**
```json
// Request
{
  "email": "rahul@company.com",
  "password": "securepassword123"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "user_id",
    "name": "Rahul Sharma",
    "role": "new_developer",
    "workspace_id": "ws_id"
  }
}
```

---

### 5.3 Knowledge Graph Endpoints

```
GET    /api/v1/graph/query               Query the knowledge graph
GET    /api/v1/graph/component/{id}      Get component details
GET    /api/v1/graph/search              Search components by name
GET    /api/v1/graph/experts/{topic}     Find experts for a topic
GET    /api/v1/graph/gaps                Get knowledge gaps
POST   /api/v1/graph/ingest              Trigger manual ingestion
GET    /api/v1/graph/stats               Get graph statistics
```

**GET /api/v1/graph/component/{id}**
```json
// Response 200
{
  "id": "component_uuid",
  "name": "retry_payment",
  "type": "function",
  "file_path": "src/payments/retry_handler.py",
  "language": "python",
  "is_deprecated": false,
  "complexity": 7,
  "connections": {
    "depends_on": ["stripe_api_call", "db_update_payment"],
    "implemented_by": ["Sarah Chen"],
    "documented_in": ["Payment Architecture Doc"],
    "discussed_in": ["Slack: #engineering Feb 8"]
  },
  "experts": [
    {
      "name": "Sarah Chen",
      "email": "sarah@company.com",
      "commit_count": 8
    }
  ],
  "recent_changes": [
    {
      "commit_sha": "abc123",
      "message": "Fix retry timing bug",
      "author": "Sarah Chen",
      "date": "2026-02-08"
    }
  ]
}
```

---

### 5.4 AI Chat Endpoints

```
POST   /api/v1/chat/ask              Ask a question
GET    /api/v1/chat/sessions         List chat sessions
GET    /api/v1/chat/sessions/{id}    Get session with messages
DELETE /api/v1/chat/sessions/{id}    Delete a session
POST   /api/v1/chat/feedback         Submit answer feedback
```

**POST /api/v1/chat/ask**
```json
// Request
{
  "question": "How does the payment retry logic work?",
  "session_id": "session_uuid",  // optional, for continuing conversation
  "context_module": "payment_system"  // optional, scope the search
}

// Response 200
{
  "answer": "The payment retry system uses exponential backoff...",
  "session_id": "session_uuid",
  "sources": [
    {
      "type": "code",
      "title": "retry_handler.py",
      "file_path": "src/payments/retry_handler.py",
      "line_start": 45,
      "line_end": 89,
      "snippet": "def retry_payment(payment_id):\n    max_retries = 3..."
    },
    {
      "type": "document",
      "title": "Payment Architecture",
      "url": "confluence/payment-arch",
      "relevance_score": 0.92
    },
    {
      "type": "expert",
      "name": "Sarah Chen",
      "email": "sarah@company.com",
      "reason": "8 commits to this module"
    }
  ],
  "related_topics": [
    "Stripe API Integration",
    "Error Handling Patterns",
    "Database Transaction Management"
  ],
  "confidence_score": 0.89,
  "is_deprecated_info": false
}
```

---

### 5.5 Onboarding Endpoints

```
POST   /api/v1/onboarding/create            Create onboarding path
GET    /api/v1/onboarding/{user_id}         Get user's learning path
PUT    /api/v1/onboarding/{user_id}/path    Update/customize path
POST   /api/v1/onboarding/progress          Update module progress
GET    /api/v1/onboarding/checklist         Get Day 1 checklist
POST   /api/v1/onboarding/regenerate        AI regenerate path
```

**POST /api/v1/onboarding/create**
```json
// Request
{
  "user_id": "user_uuid",
  "developer_role": "backend",
  "experience_level": "junior",
  "repos": ["repo1", "repo2"]
}

// Response 201
{
  "path_id": "path_uuid",
  "user_id": "user_uuid",
  "estimated_days": 10,
  "modules": [
    {
      "id": "mod_uuid",
      "title": "Environment Setup",
      "status": "not_started",
      "estimated_hours": 4,
      "order": 1
    }
  ],
  "ai_generated": true,
  "created_at": "2026-02-13T10:00:00Z"
}
```

---

### 5.6 Admin Endpoints

```
GET    /api/v1/admin/dashboard          Get team overview metrics
GET    /api/v1/admin/team               List all team members
POST   /api/v1/admin/team/member        Add new team member
DELETE /api/v1/admin/team/{user_id}     Remove team member
GET    /api/v1/admin/analytics          Get detailed analytics
GET    /api/v1/admin/gaps               Get knowledge gaps report
PUT    /api/v1/admin/integrations       Update integration settings
GET    /api/v1/admin/integrations       Get integration status
```

**GET /api/v1/admin/dashboard**
```json
// Response 200
{
  "workspace_id": "ws_uuid",
  "metrics": {
    "total_developers": 20,
    "actively_onboarding": 3,
    "avg_onboarding_days": 4.2,
    "knowledge_coverage_percent": 78,
    "ai_answer_satisfaction": 0.84,
    "questions_this_week": 47
  },
  "recent_activity": [
    {
      "type": "developer_joined",
      "developer": "Rahul Sharma",
      "role": "Backend Developer",
      "timestamp": "2026-02-13T08:00:00Z"
    }
  ],
  "knowledge_gaps": [
    {
      "topic": "payment retry logic",
      "question_count": 8,
      "priority": "high"
    }
  ],
  "team_progress": [
    {
      "user_id": "user_uuid",
      "name": "Rahul Sharma",
      "role": "Backend Developer",
      "progress_percent": 45,
      "days_since_start": 3,
      "status": "on_track"
    }
  ]
}
```

---

### 5.7 Integration Endpoints

```
POST   /api/v1/integrations/github/connect      Connect GitHub
POST   /api/v1/integrations/slack/connect       Connect Slack
POST   /api/v1/integrations/confluence/connect  Connect Confluence
DELETE /api/v1/integrations/{type}/disconnect   Disconnect integration
POST   /api/v1/integrations/github/webhook      GitHub webhook receiver
GET    /api/v1/integrations/status              Get all integration statuses
POST   /api/v1/integrations/sync                Manual sync trigger
```

### 5.8 API Response Standards

**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User with ID xyz not found",
    "details": {}
  }
}
```

**Standard HTTP Status Codes:**
```
200 → OK (successful GET, PUT)
201 → Created (successful POST)
204 → No Content (successful DELETE)
400 → Bad Request (validation error)
401 → Unauthorized (missing/invalid token)
403 → Forbidden (insufficient permissions)
404 → Not Found
422 → Unprocessable Entity (business logic error)
429 → Too Many Requests (rate limit exceeded)
500 → Internal Server Error
```

---

## 6. AI & Agent Design

### 6.1 RAG Pipeline Design

The core AI feature of Prism is the RAG (Retrieval Augmented Generation) pipeline that powers the chat interface:

```
User Question
     │
     ▼
┌─────────────────────────────┐
│  1. Query Understanding      │
│  Intent classification +     │
│  Entity extraction           │
│  (LangChain + GPT-4)        │
└─────────────┬───────────────┘
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
┌──────────┐    ┌─────────────┐
│ Graph    │    │  Semantic   │
│ Traversal│    │  Search     │
│ (Neo4j)  │    │ (ChromaDB)  │
└────┬─────┘    └──────┬──────┘
     │                 │
     └────────┬────────┘
              │
              ▼
┌─────────────────────────────┐
│  3. Context Assembly         │
│  Merge + rank results        │
│  Add code snippets           │
│  Identify experts            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  4. Answer Generation        │
│  GPT-4 with context          │
│  Grounded, cited response    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  5. Post-Processing          │
│  Add source citations        │
│  Check for deprecated info   │
│  Suggest related topics      │
└─────────────────────────────┘
              │
              ▼
         Response to User
```

### 6.2 Learning Path Generation

```python
LEARNING_PATH_PROMPT = """
You are an expert engineering onboarding specialist.

Given:
- Developer Role: {role}
- Experience Level: {experience}
- Repository Analysis: {repo_analysis}
- Team Size: {team_size}

Generate a personalized learning path with:
1. Modules ordered by dependency (prerequisites first)
2. Time estimates based on complexity and experience
3. Specific files to review for each module
4. Key concepts to understand per module
5. Suggested experts to meet per module

Output as structured JSON following this schema: {schema}

Focus on practical, hands-on learning.
Prioritize understanding systems the developer will work with daily.
"""
```

### 6.3 Knowledge Gap Detection

The system automatically identifies knowledge gaps by:

```python
def detect_knowledge_gaps(workspace_id: str) -> List[KnowledgeGap]:
    """
    Algorithm:
    1. Get all questions asked in last 30 days
    2. Cluster similar questions by topic (embedding similarity)
    3. For each cluster with >3 questions:
       a. Check if topic has documentation in graph
       b. If no docs: flag as HIGH priority gap
       c. If has docs but still asked often: flag as MEDIUM (outdated docs?)
    4. Sort by frequency + business impact
    5. Return prioritized gap list
    """
```

### 6.4 Feedback Learning Loop

```
User gives thumbs down on answer
          │
          ▼
Log: question + bad_answer + context_used
          │
          ▼
Weekly batch job:
  - Analyze patterns in poor answers
  - Identify: wrong context retrieved?
              insufficient documentation?
              wrong graph relationships?
          │
          ▼
Auto-improve:
  - Update confidence scores in graph
  - Flag components needing better docs
  - Adjust retrieval weights
          │
          ▼
Better answers over time 🔄
```

---

## 7. Data Flow Design

### 7.1 Initial Knowledge Graph Build Flow

```
Admin connects GitHub repo
          │
          ▼
GitHub API: fetch all files
          │
          ▼
For each code file:
  ├─ Tree-sitter: parse AST
  ├─ Extract: functions, classes, imports
  ├─ Generate embeddings (Sentence Transformers)
  ├─ Store entities → Neo4j
  └─ Store embeddings → ChromaDB

For each commit history:
  ├─ Extract: authors per file/function
  └─ Create AUTHORED_BY relationships → Neo4j

For each PR / issue:
  ├─ NLP: extract discussed components
  ├─ Generate embeddings
  └─ Create DISCUSSED_IN relationships → Neo4j

For Slack channels:
  ├─ Fetch messages (last 90 days)
  ├─ NLP: identify technical discussions
  ├─ Link to code components
  └─ Store as Document nodes → Neo4j

For documentation:
  ├─ Chunk into 512-token segments
  ├─ Generate embeddings per chunk
  ├─ Store chunks → ChromaDB
  └─ Create DOCUMENTED_BY relationships → Neo4j

          │
          ▼
Knowledge Graph Ready ✅
Estimated time: 15-30 min for medium repo
```

### 7.2 Real-Time Update Flow (On Code Push)

```
Developer pushes to GitHub
          │
          ▼
GitHub webhook → POST /api/v1/integrations/github/webhook
          │
          ▼
Background job triggered (Celery/FastAPI BackgroundTasks)
          │
          ▼
Fetch changed files from commit
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
New files   Modified files
    │           │
    ▼           ▼
Parse AST   Diff old vs new AST
    │           │
    ▼           ▼
Create new  Update existing nodes
nodes       in Neo4j + ChromaDB
    │           │
    └─────┬─────┘
          │
          ▼
Check for deprecated components
          │
          ▼
Update confidence scores
          │
          ▼
Notify affected onboarding paths
(if module content changed)
          │
          ▼
Graph updated ✅ (< 5 minutes)
```

### 7.3 Question-Answer Flow

```
Developer: "How does JWT auth work?"
          │
          ▼
POST /api/v1/chat/ask
          │
          ▼
Auth middleware: verify JWT token
          │
          ▼
LangChain Agent receives question
          │
          ▼
Step 1: Intent Understanding
  GPT-4: "User wants to understand JWT
          authentication implementation"
  Extracted entities: ["JWT", "auth", "authentication"]
          │
          ▼
Step 2: Parallel Retrieval
  ┌───────────────────┬──────────────────┐
  │  Neo4j Graph      │  ChromaDB Vector │
  │  Query:           │  Search:         │
  │  MATCH (c)-[r]-() │  "JWT auth       │
  │  WHERE c.name     │   implementation"│
  │  CONTAINS "auth"  │                  │
  └───────────────────┴──────────────────┘
          │
          ▼
Step 3: Context Assembly
  - 3 relevant code snippets
  - 2 documentation chunks
  - 1 Slack discussion
  - 2 expert names
  Total context: ~2000 tokens
          │
          ▼
Step 4: GPT-4 Generation
  System: "You are Prism, a code mentor.
           Answer based ONLY on provided context.
           Always cite your sources."
  Context: [assembled context]
  Question: "How does JWT auth work?"
          │
          ▼
Step 5: Post-Processing
  - Extract citations from response
  - Check if any sources are deprecated
  - Generate related topic suggestions
  - Calculate confidence score
          │
          ▼
Response returned to user ✅ (< 3 seconds)
```

### 7.4 New Developer Onboarding Flow

```
Admin: Add Rahul (Backend, Junior)
          │
          ▼
POST /api/v1/onboarding/create
          │
          ▼
Personalization Engine:
  1. Load "backend" role template
  2. Analyze workspace repos via Knowledge Graph
  3. Identify: critical paths, most complex modules,
               key people, recommended order
  4. Adjust for "junior" experience:
     - Add more explanatory resources
     - Increase time estimates
     - Add more expert introductions
  5. GPT-4: Generate module descriptions
          │
          ▼
Learning Path saved to MongoDB
          │
          ▼
Welcome email sent to Rahul
          │
          ▼
Rahul logs in → Sees personalized dashboard
          │
          ▼
Day 1-2: Environment Setup module
  - Automated setup scripts run
  - AI guides through any errors
  - Questions answered via chat
          │
          ▼
Day 3-4: Codebase Architecture module
  - Interactive knowledge graph exploration
  - AI explains system components
  - Meet recommended experts
          │
          ▼
Progress tracked continuously
Path adapted based on:
  - Questions asked (identify confusion)
  - Completion speed (fast → advance faster)
  - Stuck points (add extra resources)
          │
          ▼
Day 4-5: First PR merged ✅
```

---

## 8. UI/UX Design

### 8.1 Design Philosophy & Principles

Prism's UI is designed with three core principles:

1. **Clarity Over Complexity**: Information-dense but never overwhelming
2. **Speed & Efficiency**: Developers should find answers in seconds, not minutes
3. **Progressive Disclosure**: Show what's needed now, reveal depth on demand

### 8.2 Design System

#### 8.2.1 Color Palette

| Property | Value |
|----------|-------|
| Primary Background | `#0F172A` (dark navy) |
| Secondary Background | `#1E293B` (dark slate) |
| Card Background | `#1E293B` with border `#334155` |
| Primary Accent | `#6C63FF` (purple) |
| Secondary Accent | `#0EA5E9` (blue) |
| Success | `#22C55E` (green) |
| Warning | `#F59E0B` (amber) |
| Error | `#EF4444` (red) |
| Text Primary | `#F8FAFC` (white) |
| Text Secondary | `#94A3B8` (muted) |
| Font | Inter or Geist Sans |
| Border Radius | 8px (cards), 4px (inputs), 999px (pills) |
| Shadow | `0 4px 6px rgba(0,0,0,0.3)` |

### 8.2 Component Library

```
Built on: shadcn/ui + Tailwind CSS

Key Components:
├── Navigation
│   ├── TopNavbar
│   └── SidebarNav
├── Dashboard
│   ├── StatCard
│   ├── ActivityFeed
│   ├── ProgressTable
│   └── KnowledgeGapCard
├── Learning
│   ├── LearningPathTimeline
│   ├── ModuleCard
│   ├── ProgressBar
│   └── ResourceLink
├── Chat
│   ├── ChatBubble (user + AI variants)
│   ├── CodeSnippet (with syntax highlight)
│   ├── SourceCitation
│   ├── TopicPill
│   └── ChatInput
├── Graph
│   ├── GraphCanvas (React Flow)
│   ├── NodeCard
│   ├── EdgeLabel
│   └── GraphControls
└── Common
    ├── Button (primary, secondary, ghost)
    ├── Badge (status variants)
    ├── Avatar
    ├── Modal
    └── Toast
```

### 8.3 Key Screen Layouts

#### Screen 1: Developer Dashboard
```
┌─────────────────────────────────────────────────┐
│ [Prism Logo]    Dashboard  Chat  Graph  [Avatar] │  ← Navbar
├──────────────┬──────────────────────────────────┤
│ Learning     │  Welcome Rahul! Day 3 🎉           │
│ Path         │  ████████████░░░░ 45% Complete    │
│              ├───────────────┬──────────────────┤
│ ✅ Setup     │ Current Module│  Today's Goals   │
│ ✅ Overview  │ ─────────────  │  ─────────────── │
│ 🔄 Auth ←── │ Auth System   │  ☐ Auth module   │
│ ⏳ Payment  │ ██████░░░ 60% │  ☐ Review PR     │
│ ⏳ Deploy   │ [Continue →]  │  ☐ Meet Sarah    │
│              ├───────────────┴──────────────────┤
│ [+ Add]     │  Ask Prism AI...          [Ask →] │
└──────────────┴──────────────────────────────────┘
```

#### Screen 2: AI Chat Interface
```
┌─────────────────────────────────────────────────┐
│ [Prism]  AI Chat                   [Clear Chat] │
├────────────────┬────────────────────────────────┤
│ Recent Chats   │  [Context: Auth Module]        │
│ ─────────────  │                                │
│ > How auth...  │  👤 How does JWT auth work?    │
│   Payment...   │                                │
│   Deploy...    │  🤖 Prism AI                   │
│                │  JWT auth uses a 3-step flow:  │
│                │  ┌──────────────────────────┐  │
│                │  │ def verify_token(token): │  │
│                │  │   payload = jwt.decode() │  │
│                │  └──────────────────────────┘  │
│                │  [📄 Auth Doc][👤 @sarah][🔗PR]│
│                │  [JWT Tokens][Sessions][OAuth] │
│ [+ New Chat]  │  Was this helpful? [👍] [👎]   │
├────────────────┴────────────────────────────────┤
│ [📎]  Ask anything about your codebase...  [→] │
└─────────────────────────────────────────────────┘
```

#### Screen 3: Knowledge Graph Explorer
```
┌─────────────────────────────────────────────────┐
│ [Prism]  Knowledge Graph                        │
├─────────────────────────────────────────────────┤
│ [🔍 Search...]  [All▼] [Code] [People] [Docs]  │
├────────────────────────────┬────────────────────┤
│   Graph Canvas             │  Payment System    │
│                            │  Core Component    │
│     [Stripe]──┐            │  ─────────────     │
│               │            │  Overview Files    │
│         [Payment]          │  People Discuss    │
│        /    \   \          │                    │
│   [Retry] [DB] [@sarah]    │  📄 handler.py     │
│       \                    │  📄 retry.py       │
│      [Design Doc]          │  📄 models.py      │
│                            │  ────────────────  │
│  [+][-][⟲]                 │  👤 Sarah (8)      │
│  🔵Code 🟢People 🟣Docs   │  👤 Mike (3)       │
│                            │  ⚠️ v1 deprecated  │
└────────────────────────────┴────────────────────┘
```

---

## 9. Security Design

### 9.1 Authentication Flow

```
User Login Request
      │
      ▼
Validate email + password
      │
      ▼
Check rate limit (5 attempts / 15 minutes)
      │
      ▼
Verify bcrypt password hash
      │
      ▼
Generate Access Token (JWT, 24h expiry)
Generate Refresh Token (JWT, 7d expiry)
      │
      ▼
Store refresh token hash in Redis
      │
      ▼
Return tokens to client
      │
Client stores:
  - Access token: Memory / sessionStorage
  - Refresh token: HttpOnly cookie (NOT localStorage)
```

### 9.2 Request Authorization Flow

```
Every API Request
      │
      ▼
Extract Bearer token from Authorization header
      │
      ▼
Verify JWT signature + expiry
      │
      ▼
Extract role from token payload
      │
      ▼
Check RBAC permissions for route:

Route permissions:
  /admin/* → role must be "admin"
  /onboarding/* → role must be "admin" or "new_developer"
  /chat/* → any authenticated user
  /graph/* → any authenticated user
  /integrations/* → role must be "admin"
      │
      ▼
Verify workspace_id matches resource
(users cannot access other workspaces' data)
      │
      ▼
Request proceeds ✅
```

### 9.3 Data Security Measures

| Concern | Solution |
|---------|----------|
| Password storage | bcrypt with salt rounds=12 |
| API keys in transit | TLS 1.3 everywhere |
| API keys at rest | AES-256 encrypted in MongoDB |
| Source code privacy | Processed locally, only metadata sent to LLM |
| LLM prompt injection | Input sanitization + system prompt hardening |
| NoSQL injection | Pydantic validation + pymongo parameterized queries |
| XSS | React auto-escapes, CSP headers set |
| CSRF | SameSite cookie + CORS origin whitelist |
| Secrets management | Environment variables + Python-dotenv (dev), Secrets manager (prod) |

### 9.4 Rate Limiting Strategy

```python
RATE_LIMITS = {
    "/auth/login":        "5/15min",   # Brute force protection
    "/auth/register":     "3/hour",    # Spam protection
    "/chat/ask":          "20/min",    # AI cost control
    "/graph/ingest":      "5/hour",    # Resource protection
    "/integrations/sync": "10/hour",   # API quota protection
    "default":            "100/min"    # General endpoints
}
```

---

## 10. Deployment Design

### 10.1 Development Setup

```yaml
# docker-compose.yml
version: '3.9'
services:
  api:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - MONGODB_URL=mongodb://mongo:27017/prism
      - NEO4J_URL=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on: [mongo, neo4j, redis, chromadb]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000

  mongo:
    image: mongo:6.0
    ports: ["27017:27017"]
    volumes: ["mongo_data:/data/db"]

  neo4j:
    image: neo4j:5.0
    ports: ["7474:7474", "7687:7687"]
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes: ["neo4j_data:/data"]

  redis:
    image: redis:7.0-alpine
    ports: ["6379:6379"]

  chromadb:
    image: chromadb/chroma:latest
    ports: ["8001:8000"]
    volumes: ["chroma_data:/chroma/chroma"]

volumes:
  mongo_data:
  neo4j_data:
  chroma_data:
```

### 10.2 Production Architecture

```
Internet
    │
    ▼
Vercel CDN (Frontend - React)
    │
    ▼
Render/Railway (Backend - FastAPI)
    │
    ├─────────────────────────────┐
    │                             │
    ▼                             ▼
MongoDB Atlas              Neo4j Aura
(User Data)                (Knowledge Graph)
    │                             │
    ▼                             ▼
Upstash Redis              ChromaDB
(Cache)                    (Self-hosted on Render)
```

### 10.3 Environment Variables

```bash
# Backend (.env)

# App
APP_ENV=production
APP_SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://prism.dev,https://www.prism.dev

# MongoDB
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/prism

# Neo4j
NEO4J_URL=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Redis
REDIS_URL=rediss://user:pass@redis.upstash.io:6380

# ChromaDB
CHROMADB_HOST=localhost
CHROMADB_PORT=8001

# AI
OPENAI_API_KEY=sk-your-openai-key

# External Integrations
GITHUB_APP_ID=your-github-app-id
GITHUB_PRIVATE_KEY=your-github-private-key
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 10.4 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Prism CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=app

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with: { node-version: '18' }
      - name: Install and test
        run: |
          cd frontend && npm install && npm test

  deploy:
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Render (Backend)
        run: curl ${{ secrets.RENDER_DEPLOY_HOOK }}
      - name: Deploy to Vercel (Frontend)
        run: vercel --prod --token ${{ secrets.VERCEL_TOKEN }}
```

---

## 11. Tech Stack Summary

### 11.1 Complete Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React | 18.x | UI framework |
| | TypeScript | 5.x | Type safety |
| | Vite | 5.x | Build tool |
| | Tailwind CSS | 3.x | Styling |
| | shadcn/ui | Latest | Component library |
| | React Flow | 11.x | Knowledge graph viz |
| | React Query | 5.x | Data fetching/caching |
| | Recharts | 2.x | Analytics charts |
| | Axios | 1.x | HTTP client |
| **Backend** | Python | 3.11 | Core language |
| | FastAPI | 0.104 | REST API framework |
| | Pydantic | 2.x | Data validation |
| | Uvicorn | 0.24 | ASGI server |
| | Python-Jose | 3.x | JWT tokens |
| | Passlib | 1.7 | Password hashing |
| **AI/ML** | LangChain | 0.1.x | AI orchestration |
| | OpenAI GPT-4 | API | Language model |
| | Sentence Transformers | 2.x | Text embeddings |
| | spaCy | 3.x | NLP processing |
| | Tree-sitter | 0.20 | Code AST parsing |
| **Databases** | Neo4j | 5.x | Knowledge graph |
| | ChromaDB | 0.4 | Vector embeddings |
| | MongoDB | 6.x | Application data |
| | Redis | 7.x | Caching |
| **MongoDB ODM** | Beanie | 1.x | Async MongoDB ODM |
| | Motor | 3.x | Async MongoDB driver |
| **Integrations** | PyGithub | 1.x | GitHub API |
| | Slack SDK | 3.x | Slack API |
| | GitPython | 3.x | Git operations |
| **DevOps** | Docker | 24.x | Containerization |
| | Docker Compose | 2.x | Local orchestration |
| | GitHub Actions | — | CI/CD pipeline |
| | Pytest | 7.x | Backend testing |
| | Black | 23.x | Python formatter |
| | ESLint | 8.x | JS/TS linter |
| **Deployment** | Vercel | — | Frontend hosting |
| | Render/Railway | — | Backend hosting |
| | MongoDB Atlas | — | Managed MongoDB |
| | Neo4j Aura | — | Managed Neo4j |
| | Upstash Redis | — | Managed Redis |

### 11.2 Project Folder Structure

```
prism/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── core/
│   │   │   ├── config.py           # Environment config
│   │   │   ├── security.py         # JWT + auth helpers
│   │   │   └── database.py         # DB connection managers
│   │   ├── models/
│   │   │   ├── user.py             # Beanie/MongoDB models
│   │   │   ├── workspace.py
│   │   │   ├── learning_path.py
│   │   │   └── chat_session.py
│   │   ├── routers/
│   │   │   ├── auth.py             # Auth endpoints
│   │   │   ├── graph.py            # Knowledge graph endpoints
│   │   │   ├── chat.py             # AI chat endpoints
│   │   │   ├── onboarding.py       # Onboarding endpoints
│   │   │   ├── admin.py            # Admin endpoints
│   │   │   └── integrations.py     # Integration endpoints
│   │   ├── services/
│   │   │   ├── knowledge_graph.py  # Neo4j service
│   │   │   ├── vector_store.py     # ChromaDB service
│   │   │   ├── ai_agent.py         # LangChain agent
│   │   │   ├── personalization.py  # Learning path generator
│   │   │   └── ingestion/
│   │   │       ├── code_analyzer.py
│   │   │       ├── doc_processor.py
│   │   │       └── comm_miner.py
│   │   └── utils/
│   │       ├── embeddings.py
│   │       └── helpers.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── StatCard.tsx
│   │   │   │   ├── ProgressTable.tsx
│   │   │   │   └── ActivityFeed.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatBubble.tsx
│   │   │   │   ├── CodeSnippet.tsx
│   │   │   │   └── ChatInput.tsx
│   │   │   └── graph/
│   │   │       ├── GraphCanvas.tsx
│   │   │       └── NodeDetails.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Chat.tsx
│   │   │   ├── Graph.tsx
│   │   │   └── Admin.tsx
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── deploy.yml
├── requirements.md
└── design.md
```

---

## 12. Design Decisions & Rationale

### 12.1 Why MongoDB over PostgreSQL?

| Factor | MongoDB Advantage for Prism |
|--------|---------------------------|
| Learning path structure | Variable nested modules fit documents naturally |
| Schema flexibility | Easy to add fields during hackathon iterations |
| Developer experience | JSON-in = JSON-out, no ORM complexity |
| Free tier | MongoDB Atlas 512MB is sufficient for MVP |
| Python integration | Motor + Beanie give excellent async FastAPI support |

### 12.2 Why Neo4j for Knowledge Graph?

| Factor | Rationale |
|--------|-----------|
| Graph-native queries | Cypher is far more expressive than SQL for relationship traversal |
| Performance | Graph traversal is O(relationship count), not O(table size) |
| Visualization | Built-in graph browser for debugging |
| Managed option | Neo4j Aura has a free tier for MVP |
| Industry standard | Most widely used graph database |

### 12.3 Why LangChain over custom LLM integration?

| Factor | Rationale |
|--------|-----------|
| Tooling | Built-in tools for RAG, memory, agents |
| Flexibility | Easy to swap GPT-4 for another model later |
| Community | Large ecosystem of integrations |
| Speed | Faster to build reliable AI pipelines |

### 12.4 Why FastAPI over Django/Flask?

| Factor | Rationale |
|--------|-----------|
| Performance | Async-native, fastest Python web framework |
| Auto-docs | Swagger UI generated automatically from type hints |
| Type safety | Pydantic integration = validated inputs everywhere |
| Modern | Designed for modern API patterns (async, streaming) |

### 12.5 Why ChromaDB over Pinecone?

| Factor | Rationale |
|--------|-----------|
| Cost | Self-hosted = free (vs Pinecone's paid tiers) |
| Simplicity | Easy to run locally in Docker |
| Sufficient scale | MVP scale doesn't need Pinecone's distributed power |
| Migration path | Can migrate to Pinecone later if needed |

---

*Document Version: 1.0*  
*Last Updated: February 2026*  
*Project: Prism — AI for Bharat by Amazon*  
*Status: Draft for Hackathon Submission*