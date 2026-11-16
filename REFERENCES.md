# CareCoord – Project References & Foundational Literature

This document contains 10 key technical and academic references that serve as the foundation for the **CareCoord** (Agentic Healthcare Workflow System) project architecture, framework selection, and clinical safety design.

---

### 1. LangGraph: Building Stateful Multi-Agent Applications
* **Publisher / Platform**: LangChain AI
* **Hyperlink**: [LangGraph Official Documentation](https://langchain-ai.github.io/langgraph/)
* **Relevance to CareCoord**: Used in `backend/agents/graph.py` as the stateful multi-agent engine. Enables graph-based workflow transitions (`CareCoordState`), node-to-node routing (`parse_request` $\rightarrow$ `coordinator` $\rightarrow$ specialized agents $\rightarrow$ `validation`), and cyclic state management.

### 2. FastAPI: Modern High-Performance Python Web Framework
* **Publisher / Platform**: FastAPI / Tiangolo
* **Hyperlink**: [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
* **Relevance to CareCoord**: Powers the backend REST API layer (`backend/main.py`), providing asynchronous API endpoints, auto-generated OpenAPI (Swagger) documentation, and dependency injection for database sessions.

### 3. Google Gemini API: Generative AI for Structured Output & NL Processing
* **Publisher / Platform**: Google AI for Developers
* **Hyperlink**: [Google Gemini API Documentation](https://ai.google.dev/docs)
* **Relevance to CareCoord**: Utilized in `backend/services/llm_parser_service.py` to parse unstructured natural language queries into validated structured JSON models (`WorkflowParseResult`).

### 4. WHO Guidance on Governance and Safety of AI in Healthcare
* **Publisher / Platform**: World Health Organization (WHO)
* **Hyperlink**: [WHO Guidance on Artificial Intelligence in Health](https://www.who.int/publications/i/item/9789240029200)
* **Relevance to CareCoord**: Informs the **Human-in-the-Loop (HITL)** safety boundary (`REQUIRES_HUMAN_APPROVAL`), ensuring AI agents only recommend operational changes while human hospital staff retain sole authority for database mutations.

### 5. SQLAlchemy 2.0: Unified Python ORM & Database Toolkit
* **Publisher / Platform**: SQLAlchemy Project
* **Hyperlink**: [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
* **Relevance to CareCoord**: Manages relational database entities (`backend/database/models.py`) including `Patient`, `Doctor`, `Appointment`, `Bed`, `Emergency`, `WorkflowRun`, and `WorkflowEvent` within SQLite.

### 6. Pydantic v2: Data Validation using Python Type Hints
* **Publisher / Platform**: Pydantic Services Inc.
* **Hyperlink**: [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
* **Relevance to CareCoord**: Enforces strict payload validation across API endpoints (`backend/schemas/`) and agent graph state schemas, preventing invalid data entry (e.g. malformed phone numbers or invalid age values).

### 7. Vite: Next Generation Frontend Tooling
* **Publisher / Platform**: Vite Project
* **Hyperlink**: [Vite Official Documentation](https://vite.dev/)
* **Relevance to CareCoord**: Provides fast HMR (Hot Module Replacement) and optimized production bundling for the frontend dashboard (`frontend/vite.config.js`).

### 8. React 18: Declarative User Interface Framework
* **Publisher / Platform**: Meta / React Open Source
* **Hyperlink**: [React 18 Official Documentation](https://react.dev/)
* **Relevance to CareCoord**: Powers the single-page application dashboard (`frontend/src/App.jsx`), facilitating real-time UI state updates, interactive graph visualizers, and workflow history tables.

### 9. Tailwind CSS: Utility-First CSS Framework
* **Publisher / Platform**: Tailwind Labs
* **Hyperlink**: [Tailwind CSS Documentation](https://tailwindcss.com/)
* **Relevance to CareCoord**: Implements the dark-theme Command Center design system, responsive KPI cards, status badges, progress bars, and modal drawers.

### 10. Multi-Agent Resource Scheduling in Hospital Operations (Academic Paper)
* **Publisher / Platform**: National Institutes of Health / PubMed Central (PMC)
* **Hyperlink**: [Agent-based Simulation for Hospital Resource Allocation](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7323861/)
* **Relevance to CareCoord**: Establishes theoretical framework for agent-based bed management, emergency triage prioritization, and operational bottleneck reduction in clinical environments.
