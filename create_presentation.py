import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_dark_carecoord_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Premium Dark Theme Color Palette
    BLACK_BG = RGBColor(11, 15, 25)         # Deep Obsidian Black (#0B0F19)
    BANNER_BG = RGBColor(18, 24, 38)        # Dark Slate Banner (#121826)
    CARD_BG = RGBColor(22, 30, 46)          # Translucent Dark Glass Card (#161E2E)
    BORDER_GLOW = RGBColor(38, 52, 77)      # Slate Border (#26344D)
    
    # High-Contrast Text Colors
    WHITE = RGBColor(255, 255, 255)         # Pure White
    TEXT_BODY = RGBColor(226, 232, 240)     # Light Slate (#E2E8F0)
    TEXT_MUTED = RGBColor(148, 163, 184)    # Muted Slate (#94A3B8)
    
    # Vibrantly Glowing Accents
    CYAN_ACCENT = RGBColor(56, 189, 248)    # Neon Sky Cyan (#38BDF8)
    EMERALD_ACCENT = RGBColor(52, 211, 153) # Neon Emerald Green (#34D399)
    ROSE_ACCENT = RGBColor(251, 113, 133)   # Neon Rose Red (#FB7185)
    PURPLE_ACCENT = RGBColor(192, 132, 252) # Neon Purple (#C084FC)
    AMBER_ACCENT = RGBColor(251, 191, 36)   # Neon Amber Gold (#FBBF24)

    FONT_MAIN = "Segoe UI"

    def add_blank_dark_slide():
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)
        # Add deep obsidian black background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BLACK_BG
        bg.line.color.rgb = BLACK_BG
        return slide

    def add_dark_header(slide, title_text, category_text="CARECOORD | MAJOR PROJECT DEFENSE"):
        # Header banner rectangle
        banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.15))
        banner.fill.solid()
        banner.fill.fore_color.rgb = BANNER_BG
        banner.line.color.rgb = BORDER_GLOW

        # Glowing accent bottom line
        accent_line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.12), Inches(13.333), Inches(0.04))
        accent_line.fill.solid()
        accent_line.fill.fore_color.rgb = CYAN_ACCENT
        accent_line.line.color.rgb = CYAN_ACCENT

        tf = banner.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.word_wrap = True
        tf.margin_left = Inches(0.6)
        tf.margin_top = Inches(0.1)

        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.name = FONT_MAIN
        p0.font.size = Pt(10)
        p0.font.bold = True
        p0.font.color.rgb = CYAN_ACCENT

        p1 = tf.add_paragraph()
        p1.text = title_text
        p1.font.name = FONT_MAIN
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = WHITE

    def add_dark_card(slide, left, top, width, height, title, items, title_color=CYAN_ACCENT, border_color=BORDER_GLOW):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.35)
        tf.margin_right = Inches(0.35)
        tf.margin_top = Inches(0.3)
        tf.margin_bottom = Inches(0.3)

        if title:
            p = tf.paragraphs[0]
            p.text = title
            p.font.name = FONT_MAIN
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = title_color
            p.space_after = Pt(12)

        for i, item in enumerate(items):
            p = tf.add_paragraph() if (title or i > 0) else tf.paragraphs[0]
            p.font.name = FONT_MAIN
            p.space_after = Pt(8)
            
            # Format title/colon bold highlights if present
            if ":" in item and not item.startswith("  -"):
                parts = item.split(":", 1)
                run1 = p.add_run()
                run1.text = "• " + parts[0] + ":"
                run1.font.bold = True
                run1.font.size = Pt(13)
                run1.font.color.rgb = WHITE
                
                run2 = p.add_run()
                run2.text = parts[1]
                run2.font.size = Pt(13)
                run2.font.color.rgb = TEXT_BODY
            else:
                p.text = "• " + item if not item.startswith("  -") else "   - " + item[4:]
                p.font.size = Pt(13)
                p.font.color.rgb = TEXT_BODY

    # ----------------------------------------------------
    # SLIDE 1: TITLE SLIDE (PREMIUM DARK HERO)
    # ----------------------------------------------------
    slide1 = add_blank_dark_slide()

    # Glowing side bar
    side_bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(2.0), Inches(0.18), Inches(3.6))
    side_bar.fill.solid()
    side_bar.fill.fore_color.rgb = CYAN_ACCENT
    side_bar.line.color.rgb = CYAN_ACCENT

    # Main title text frame
    tb = slide1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11.0), Inches(4.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "CSE MAJOR PROJECT PRESENTATION"
    p0.font.name = FONT_MAIN
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_ACCENT
    p0.space_after = Pt(14)

    p1 = tf.add_paragraph()
    p1.text = "CareCoord: Agentic Healthcare Workflow System"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(34)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_after = Pt(14)

    p2 = tf.add_paragraph()
    p2.text = "Stateful Multi-Agent Orchestration with LangGraph & Human-in-the-Loop Safety Oversight"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(18)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_after = Pt(36)

    p3 = tf.add_paragraph()
    p3.text = "Department of Computer Science & Engineering | Major Project Defense"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(15)
    p3.font.bold = True
    p3.font.color.rgb = EMERALD_ACCENT

    # ----------------------------------------------------
    # SLIDE 2: EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # ----------------------------------------------------
    slide2 = add_blank_dark_slide()
    add_dark_header(slide2, "Executive Summary & Problem Statement")

    add_dark_card(slide2, 0.8, 1.4, 5.6, 5.5, "Problem Statement in Hospital Operations", [
        "Fragmented Department Communication: Hospital units (Doctors, Beds, Admissions) operate in uncoordinated silos.",
        "Manual Resource Allocation: Staff waste critical time checking spreadsheets and unverified schedules.",
        "Delayed Emergency Triage: Critical admissions suffer delays due to lack of real-time inventory tracking.",
        "Lack of Granular Auditability: Operational workflow steps are rarely logged with millisecond execution latency."
    ], title_color=ROSE_ACCENT, border_color=ROSE_ACCENT)

    add_dark_card(slide2, 6.8, 1.4, 5.7, 5.5, "CareCoord Multi-Agent Solution", [
        "Stateful Multi-Agent Orchestration: Autonomous AI agents handling real-time hospital resource coordination.",
        "LangGraph StateGraph Engine: Cyclic graph execution with persistent state and conflict resolution.",
        "Human-in-the-Loop (HITL) Safety Boundary: AI suggests operational recommendations; human staff authorize database commits.",
        "Operational Safety Scope: Focused strictly on workflow coordination (NOT a clinical diagnosis system)."
    ], title_color=CYAN_ACCENT, border_color=CYAN_ACCENT)

    # ----------------------------------------------------
    # SLIDE 3: PHASE ROADMAP & DEVELOPMENT EVOLUTION
    # ----------------------------------------------------
    slide3 = add_blank_dark_slide()
    add_dark_header(slide3, "Implementation Roadmap Across Phases")

    add_dark_card(slide3, 0.8, 1.4, 3.6, 5.5, "Phase 1: Backend Foundation", [
        "Clean FastAPI Architecture: High-performance ASGI web framework.",
        "SQLite & SQLAlchemy 2.0: Relational DB models (Patient, Doctor, Appointment, Bed, Emergency).",
        "Pydantic v2 Schema Validation: Strict input validation schemas.",
        "Automated Verification Suite: 14-step verification suite (test_phase1.py)."
    ], title_color=CYAN_ACCENT)

    add_dark_card(slide3, 4.8, 1.4, 3.6, 5.5, "Phase 2: AI Foundation & UI V1", [
        "Natural Language Request Parser: Powered by Gemini API structured JSON outputs.",
        "Structured Intent Extraction: Parse requests into request_type, urgency, and missing parameters.",
        "V1 Single-Turn Agents: Patient, Doctor, and Appointment agents.",
        "CareCoord Dashboard V1: React + Vite + Tailwind CSS interface."
    ], title_color=AMBER_ACCENT)

    add_dark_card(slide3, 8.8, 1.4, 3.7, 5.5, "Phase 3: LangGraph Multi-Agent", [
        "Stateful Graph Engine: LangGraph StateGraph with persistent CareCoordState schema.",
        "Coordinator Agent: Central router & slot conflict solver.",
        "Validation Node: Operational rule checking & HITL flag trigger.",
        "Audit Logging & Visualizer: SQLite audit logging and live React graph visualizer."
    ], title_color=EMERALD_ACCENT)

    # ----------------------------------------------------
    # SLIDE 4: END-TO-END TARGET ARCHITECTURE
    # ----------------------------------------------------
    slide4 = add_blank_dark_slide()
    add_dark_header(slide4, "End-to-End System Target Architecture")

    add_dark_card(slide4, 0.8, 1.4, 11.7, 5.5, "System Data Flow & Agent Pipeline", [
        "1. Command Center UI (React 18 + Vite): User enters natural language request in Workflow Terminal.",
        "2. FastAPI REST Endpoint (POST /api/workflows): Receives request and initializes graph state execution.",
        "3. Request Parser Node (parse_request): Invokes Gemini LLM service to extract structured JSON entities.",
        "4. Coordinator Agent (coordinator): Evaluates required agents, resolves slot conflicts, and routes state.",
        "5. Specialized Tool Execution (patient, doctor, appointment nodes): Interacts with SQLite database services.",
        "6. Validation Node & HITL Boundary: Intercepts mutations and sets status = REQUIRES_HUMAN_APPROVAL.",
        "7. Human Approval & Commitment (POST /api/workflows/{id}/approve): Staff review and commit database mutations."
    ], title_color=PURPLE_ACCENT)

    # ----------------------------------------------------
    # SLIDE 5: LANGGRAPH STATEFUL ENGINE
    # ----------------------------------------------------
    slide5 = add_blank_dark_slide()
    add_dark_header(slide5, "LangGraph Stateful Engine & State Schema")

    add_dark_card(slide5, 0.8, 1.4, 5.6, 5.5, "CareCoordState Schema Attributes", [
        "workflow_id: Unique string tracking workflow run session.",
        "original_request: Raw natural language prompt entered by user.",
        "workflow_request: Structured JSON payload parsed by LLM.",
        "required_agents & executed_agents: Sequence calculation & progress tracking lists.",
        "execution_log: Detailed event log with latency metrics in ms.",
        "status: State lifecycle flag (RUNNING, NEEDS_CLARIFICATION, REQUIRES_HUMAN_APPROVAL, COMPLETED).",
        "iteration_count: Loop safety cap (Max 10 execution iterations)."
    ], title_color=CYAN_ACCENT)

    add_dark_card(slide5, 6.8, 1.4, 5.7, 5.5, "Node Graph Execution Pipeline", [
        "parse_request_node: Extracts request parameters via Gemini parser.",
        "coordinator_node: Decision engine evaluating required next node.",
        "doctor_agent_node: Queries doctor availability and consultation schedules.",
        "patient_agent_node: Retrieves patient medical history and consultations.",
        "appointment_agent_node: Evaluates slot availability & drafts bookings.",
        "validation_graph_node: Operational safety & HITL flag trigger.",
        "final_response_node: Compiles operational recommendation."
    ], title_color=EMERALD_ACCENT)

    # ----------------------------------------------------
    # SLIDE 6: SPECIALIZED AGENTS & TOOL LAYER
    # ----------------------------------------------------
    slide6 = add_blank_dark_slide()
    add_dark_header(slide6, "Specialized AI Agents & Tool Architecture")

    add_dark_card(slide6, 0.8, 1.4, 5.6, 2.6, "Coordinator Agent Engine", [
        "Central Decision Engine: Routes state dynamically across nodes.",
        "Clarification Handler: Flags missing attributes (NEEDS_CLARIFICATION).",
        "Conflict Resolution: Resolves doctor schedule and slot overlaps."
    ], title_color=CYAN_ACCENT)

    add_dark_card(slide6, 6.8, 1.4, 5.7, 2.6, "Doctor Agent & doctor_tools.py", [
        "Availability Queries: Filters doctors on active duty.",
        "Specialization Lookup: Searches by department (Cardiology, etc.).",
        "Shift Tracking: Inspects shift hours and assigned patient load."
    ], title_color=AMBER_ACCENT)

    add_dark_card(slide6, 0.8, 4.3, 5.6, 2.6, "Patient Agent & patient_tools.py", [
        "Demographic Lookup: Retrieves patient profiles by ID (P001).",
        "Appointment History: Fetches past and scheduled consultations.",
        "Medical Summary: Inspects chronic conditions and blood groups."
    ], title_color=EMERALD_ACCENT)

    add_dark_card(slide6, 6.8, 4.3, 5.7, 2.6, "Appointment Agent & appointment_tools.py", [
        "Slot Evaluation: Checks doctor calendar availability for target dates.",
        "Booking Draft: Constructs proposed appointment records.",
        "Validation Handoff: Transfers proposal to Validation Node."
    ], title_color=PURPLE_ACCENT)

    # ----------------------------------------------------
    # SLIDE 7: HUMAN-IN-THE-LOOP (HITL) SAFETY BOUNDARY
    # ----------------------------------------------------
    slide7 = add_blank_dark_slide()
    add_dark_header(slide7, "Human-in-the-Loop (HITL) Safety & Staff Approval")

    add_dark_card(slide7, 0.8, 1.4, 11.7, 5.5, "Operational Safety Boundary & Staff Authorization Protocol", [
        "Safety Core Boundary: AI agents are STRICTLY PROHIBITED from auto-committing database mutations.",
        "State Interception: Operations involving resource allocation halt graph execution at status = REQUIRES_HUMAN_APPROVAL.",
        "Interactive Staff Command Card (HumanApprovalCard.jsx): Displays proposed AI booking details, doctor info, slot time, and validation checks.",
        "Staff Review Actions: Authorized hospital staff inspect recommendations and click 'Approve & Commit' or 'Reject' with notes.",
        "Database Mutation API (POST /api/workflows/{id}/approve): Formally commits the appointment to SQLite and updates status to COMPLETED."
    ], title_color=ROSE_ACCENT, border_color=ROSE_ACCENT)

    # ----------------------------------------------------
    # SLIDE 8: COMMAND CENTER DASHBOARD V2
    # ----------------------------------------------------
    slide8 = add_blank_dark_slide()
    add_dark_header(slide8, "CareCoord Command Center Dashboard V2")

    add_dark_card(slide8, 0.8, 1.4, 5.6, 5.5, "Frontend UI Architecture", [
        "Tech Stack: React 18 + Vite 5 + Tailwind CSS v3.",
        "Real-Time KPI Cards: Displays active patient counts, doctor availability, bed occupancy rate, and emergencies.",
        "Bed Utilization Gauges: Progress indicators tracking ICU, General Ward, and Emergency bed capacity.",
        "Interactive Workflow Terminal: Executes NL requests with live agent execution indicators."
    ], title_color=CYAN_ACCENT)

    add_dark_card(slide8, 6.8, 1.4, 5.7, 5.5, "Live Graph Visualizer & Audit Logs", [
        "WorkflowGraphVisualizer.jsx: Interactive visual graph highlighting current active node and step progression.",
        "WorkflowDetailDrawer.jsx: Slide-over inspection drawer showing node execution latencies in ms and tool IO.",
        "Workflow History (/workflows): Complete persistent audit table listing past workflow runs and event logs."
    ], title_color=AMBER_ACCENT)

    # ----------------------------------------------------
    # SLIDE 9: AUTOMATED VERIFICATION TEST SUITES
    # ----------------------------------------------------
    slide9 = add_blank_dark_slide()
    add_dark_header(slide9, "Automated Test Suites & System Verification")

    add_dark_card(slide9, 0.8, 1.4, 3.6, 5.5, "test_phase1.py (14 Steps)", [
        "DB Seed Verification",
        "GET /health (200 OK)",
        "Database Health Metrics",
        "Patient & Doctor Lookups",
        "Bed Availability Queries",
        "Appointment & Emergency POST",
        "HTTP 422 Payload Validation",
        "HTTP 404 Error Boundary"
    ], title_color=CYAN_ACCENT)

    add_dark_card(slide9, 4.8, 1.4, 3.6, 5.5, "test_phase2.py (6 Steps)", [
        "Dashboard Summary KPIs",
        "Cardiologist Query Routing",
        "Neurologist Search Routing",
        "Patient P001 Record Lookup",
        "Incomplete Query Handling (NEEDS_CLARIFICATION)"
    ], title_color=AMBER_ACCENT)

    add_dark_card(slide9, 8.8, 1.4, 3.7, 5.5, "test_phase3.py (9 Steps)", [
        "LangGraph StateGraph Execution",
        "Primary Demo Halting at REQUIRES_HUMAN_APPROVAL",
        "Workflow Event Log Retrieval",
        "Human Approval API Execution & SQLite Commit",
        "Workflow Audit History Logging"
    ], title_color=EMERALD_ACCENT)

    # ----------------------------------------------------
    # SLIDE 10: ACADEMIC & TECHNICAL REFERENCES
    # ----------------------------------------------------
    slide10 = add_blank_dark_slide()
    add_dark_header(slide10, "Academic Literature & Foundational References")

    add_dark_card(slide10, 0.8, 1.4, 11.7, 5.5, "Peer-Reviewed Publications & Industry Frameworks", [
        "1. Topol et al. (Nature Medicine / PMC): Multiagent AI Systems in Health Care: Envisioning Next-Generation Intelligence.",
        "2. Qian et al. (arXiv:2307.07924): Communicative Agents for Software Development & Task Orchestration.",
        "3. Ben Ali et al. (Journal of Medical Systems): Healthcare Decision Support Tool: Multi-Agent System for Bed Management.",
        "4. Yeoh et al. (IEEE Transactions / arXiv): A Coordinated MDP Approach to Multi-Agent Resource Allocation.",
        "5. Amann et al. (BMC Medical Informatics): Human-in-the-Loop AI Systems for Clinical Decision Support.",
        "6. Chase et al. (LangChain Technical Reports): LangGraph Stateful Graph Execution Frameworks."
    ], title_color=PURPLE_ACCENT)

    # ----------------------------------------------------
    # SLIDE 11: CONCLUSION & FUTURE ROADMAP
    # ----------------------------------------------------
    slide11 = add_blank_dark_slide()
    add_dark_header(slide11, "Conclusion & Future Expansion Roadmap")

    add_dark_card(slide11, 0.8, 1.4, 5.6, 5.5, "Project Deliverables Summary", [
        "Clean FastAPI + SQLite backend foundation with strict Pydantic schemas.",
        "Gemini LLM natural language request parser with structured JSON output.",
        "Stateful LangGraph multi-agent engine with 10-iteration loop safety cap.",
        "Strict Human-in-the-Loop safety boundary and audit logging in SQLite.",
        "Command Center UI V2 featuring live state visualizer and history."
    ], title_color=EMERALD_ACCENT, border_color=EMERALD_ACCENT)

    add_dark_card(slide11, 6.8, 1.4, 5.7, 5.5, "Future Expansion Roadmap", [
        "Phase 4: Bed Allocation & Nurse Triage LangGraph Agent Expansion",
        "Phase 5: RAG Policy Retrieval Agent (ChromaDB + Vector Index)",
        "Phase 6: ML Resource Surge Prediction (XGBoost / Scikit-Learn)",
        "Phase 7: OR-Tools Operations & Bed Transfer Optimization",
        "Phase 8: Production Cloud Deployment & Containerization"
    ], title_color=CYAN_ACCENT)

    # Save presentation
    output_path = Path("CareCoord_Major_Project_Presentation.pptx").resolve()
    prs.save(str(output_path))
    print(f"Dark-theme Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_dark_carecoord_presentation()
