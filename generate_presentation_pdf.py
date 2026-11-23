import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display the total page count.
    Adds a professional running header and footer with page numbers.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_elements(self, page_count):
        self.saveState()
        
        primary_color = colors.HexColor("#0f172a")  # Dark slate
        accent_color = colors.HexColor("#4f46e5")   # Indigo
        muted_text = colors.HexColor("#64748b")     # Cool grey
        border_color = colors.HexColor("#cbd5e1")   # Border grey
        
        page_width, page_height = letter
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(accent_color)
            self.drawString(40, page_height - 30, "FINFLOW AI")
            self.setFont("Helvetica", 8)
            self.setFillColor(muted_text)
            self.drawString(100, page_height - 30, "|  5-Minute Technical Screen-Recording Script & Guide")
            
            self.setFont("Helvetica", 8)
            self.drawRightString(page_width - 40, page_height - 30, "LangChain Multi-Agent Close Orchestrator")
            
            self.setStrokeColor(border_color)
            self.setLineWidth(0.5)
            self.line(40, page_height - 34, page_width - 40, page_height - 34)
            
        # Footer (all pages)
        self.setStrokeColor(border_color)
        self.setLineWidth(0.5)
        self.line(40, 36, page_width - 40, 36)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(muted_text)
        self.drawString(40, 24, "FinFlow AI Presentation Playbook  •  Apex Capital Partners Portfolio Operations")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_width - 40, 24, page_str)
        
        self.restoreState()


def build_pdf(filename="FinFlow_AI_5Min_Presentation_Script.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary = "#0f172a"
    indigo = "#4f46e5"
    emerald = "#047857"
    slate = "#334155"
    muted = "#64748b"

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(primary),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor(indigo),
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Header1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor(primary),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Header2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor(indigo),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor(slate),
        spaceAfter=6,
    )

    script_action_style = ParagraphStyle(
        "ScriptAction",
        parent=styles["Normal"],
        fontName="Helvetica-BoldOblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#b45309"),  # Amber-700
        spaceBefore=3,
        spaceAfter=3,
    )

    script_speech_style = ParagraphStyle(
        "ScriptSpeech",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor(primary),
        spaceBefore=2,
        spaceAfter=8,
    )

    box_text_style = ParagraphStyle(
        "BoxText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor(slate),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(slate),
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(primary),
    )

    code_style = ParagraphStyle(
        "CodeInline",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#094c72"),
    )

    story = []

    # Title & Header Banner
    story.append(Paragraph("FINFLOW AI: 5-MINUTE TECHNICAL PRESENTATION", title_style))
    story.append(Paragraph("Multi-Agent Month-End Financial Close Orchestrator  •  Full Speaking Script & Engineering Defense", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor(indigo), spaceBefore=0, spaceAfter=10))

    # Meta Info Card
    meta_data = [
        [
            Paragraph("<b>Stack:</b> LangChain 0.3, FastAPI, Redis 7, Next.js 14, PostgreSQL", table_cell_style),
            Paragraph("<b>Target Domain:</b> PE Portfolio Financial Operations ($615M+ Aggregate Rev)", table_cell_style),
        ],
        [
            Paragraph("<b>Presentation Type:</b> 5-Min Technical Screen-Recording", table_cell_style),
            Paragraph("<b>Verified Benchmarks:</b> 78.3% Auto-Clear Rate, 53.1% Token Savings", table_cell_style),
        ]
    ]
    t_meta = Table(meta_data, colWidths=[270, 262])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # SECTION 1: Agenda & Timing Structure
    story.append(Paragraph("1. Agenda & 5-Minute Timing Breakdown", h1_style))
    
    agenda_data = [
        [
            Paragraph("<b>Time</b>", table_header_style),
            Paragraph("<b>Target Criterion</b>", table_header_style),
            Paragraph("<b>Visual Screen Focus</b>", table_header_style),
            Paragraph("<b>Core Technical Concept</b>", table_header_style),
        ],
        [
            Paragraph("0:00 - 0:45", table_cell_bold),
            Paragraph("1. Problem & Motivation", table_cell_style),
            Paragraph("Next.js Dashboard (8 Portfolio Co.)", table_cell_style),
            Paragraph("Manual close bottleneck across $615M+ revenue portfolio.", table_cell_style),
        ],
        [
            Paragraph("0:45 - 1:30", table_cell_bold),
            Paragraph("2. AI Coding Sessions", table_cell_style),
            Paragraph("VS Code project layout & tests", table_cell_style),
            Paragraph("Iterative scaffolding of models, schemas & LCEL pipelines.", table_cell_style),
        ],
        [
            Paragraph("1:30 - 2:30", table_cell_bold),
            Paragraph("3. Decomposition & LangChain", table_cell_style),
            Paragraph("<code>base.py</code>, <code>trial_balance.py</code>, <code>workflow_engine.py</code>", table_cell_style),
            Paragraph("LLM init, Prompt templates, LCEL, JsonOutputParser, 4-stage DAG.", table_cell_style),
        ],
        [
            Paragraph("2:30 - 3:30", table_cell_bold),
            Paragraph("4. Live Results & Metrics", table_cell_style),
            Paragraph("Dashboard Close Run + <code>BENCHMARK_REPORT.md</code>", table_cell_style),
            Paragraph("Real-time WebSockets, 78.3% auto-cleared, 53.1% token savings.", table_cell_style),
        ],
        [
            Paragraph("3:30 - 4:15", table_cell_bold),
            Paragraph("5. Debugging Challenges", table_cell_style),
            Paragraph("<code>base.py</code> (L111 Redis, L297 Fallback)", table_cell_style),
            Paragraph("Context window bloat solved via Redis; 429 quota failover cascade.", table_cell_style),
        ],
        [
            Paragraph("4:15 - 5:00", table_cell_bold),
            Paragraph("6. 20× Productivity Scaling", table_cell_style),
            Paragraph("Architecture overview / Git Worktrees", table_cell_style),
            Paragraph("Parallel AI coding agents against strict BaseAgent contracts.", table_cell_style),
        ],
    ]
    t_agenda = Table(agenda_data, colWidths=[65, 140, 160, 167])
    t_agenda.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(primary)),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_agenda)
    story.append(Spacer(1, 12))

    # SECTION 2: Exact Screen-Sharing Setup
    story.append(Paragraph("2. Pre-Recording Screen Setup Checklist", h1_style))
    setup_box = [
        [Paragraph("<b>Screen Split Layout:</b><br/>"
                   "• <b>Left Display Half:</b> VS Code with files pre-opened in tabs: <code>base.py</code>, <code>trial_balance.py</code>, <code>workflow_engine.py</code>, <code>BENCHMARK_REPORT.md</code>.<br/>"
                   "• <b>Right Display Half:</b> Browser on <code>http://localhost:3000</code> displaying Executive Dashboard with 8 portfolio company cards.<br/>"
                   "• <b>Background Terminal:</b> Uvicorn running on <code>localhost:8000</code> streaming real-time JSON logs.", box_text_style)]
    ]
    t_setup = Table(setup_box, colWidths=[532])
    t_setup.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ecfdf5")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#10b981")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_setup)
    story.append(Spacer(1, 14))

    # SECTION 3: Word-for-Word Speaking Script
    story.append(Paragraph("3. Full 5-Minute Speaking Script with Visual Stage Directions", h1_style))
    story.append(Paragraph("<i>Speak naturally with authoritative developer presence. Keep pace at ~135 words/minute.</i>", body_style))

    # Segment 1
    story.append(Paragraph("[0:00 - 0:45] Criterion 1: The Problem & Why I Built FinFlow AI", h2_style))
    story.append(Paragraph("[ACTION: Share screen. Show Next.js Dashboard at localhost:3000. Cursor points to the 8 portfolio operating companies.]", script_action_style))
    story.append(Paragraph('"Hi everyone, I’m excited to show you <b>FinFlow AI</b>, an autonomous multi-agent financial orchestration platform I built to solve one of the biggest operational bottlenecks in private equity: <b>month-end financial closing</b>.<br/><br/>'
                           'In private equity firms like Apex Capital Partners, you have holding companies managing 8 or more distinct operating companies—in our case, representing over $615 million in aggregate revenue. Every single month, financial controllers burn 10 to 15 business days manually reconciling thousands of trial balance lines, hunting down bilateral intercompany mismatches, verifying amortizations, and checking ASC 606 revenue timing in massive spreadsheets.<br/><br/>'
                           'Humans are slow at deterministic math but great at high-level judgment. I built FinFlow AI to flip that equation: specialized AI agents execute deterministic accounting checks and deep LLM variance analysis autonomously, escalating only true anomalies to human controllers."', script_speech_style))

    # Segment 2
    story.append(Paragraph("[0:45 - 1:30] Criterion 2: My AI Coding Sessions & Assistant Workflow", h2_style))
    story.append(Paragraph("[ACTION: Switch to VS Code. Briefly expand the backend directory tree showing models, agents, and services.]", script_action_style))
    story.append(Paragraph('"To build this system rapidly, I used an AI-augmented development workflow, pairing with AI coding assistants as specialized architectural sounding boards.<br/><br/>'
                           'Rather than asking an AI to \'build an accounting system\' in one vague prompt, I broke my coding sessions into rigorous, modular loops:<br/>'
                           'First, I prompted the assistant to scaffold strongly-typed SQLAlchemy schemas for multi-entity ledgers, journal entries, and audit logs.<br/>'
                           'Second, I designed an abstract <code>BaseAgent</code> class, enforcing that every domain agent follows an identical contract: an asynchronous <code>execute</code> method, unified Redis shared memory, and a LangChain LCEL chain.<br/><br/>'
                           'Whenever an assistant generated code, I immediately challenged it on deterministic accuracy. In accounting, an LLM cannot be allowed to hallucinate a debit/credit balance. So I used the AI assistant to write deterministic validation functions first, using the LLM strictly for contextual reasoning, variance narratives, and ASC 606 compliance evaluation."', script_speech_style))

    # Segment 3
    story.append(Paragraph("[1:30 - 2:30] Criterion 3: Decomposition & LangChain Implementation", h2_style))
    story.append(Paragraph("[ACTION: Open backend/app/agents/base.py. Scroll to line 52 (get_llm_list), then line 284 (call_llm). Then switch to trial_balance.py and workflow_engine.py.]", script_action_style))
    story.append(Paragraph('"Let’s look at how this is implemented under the hood using <b>LangChain</b>.<br/><br/>'
                           'Here in <code>backend/app/agents/base.py</code>, we handle <b>LLM Initialization</b> dynamically across multiple providers. We configure Anthropic Claude Sonnet as our primary engine, with automatic failover to OpenAI GPT-4o, Google Gemini, and Groq LLaMA-3.3.<br/><br/>'
                           'In lines 290 to 305, you can see our <b>Prompt Template</b> and <b>LCEL chain composition</b>:<br/>'
                           '<code>template = ChatPromptTemplate.from_messages([("system", system), ("human", prompt)])</code><br/>'
                           '<code>chain = template | llm_instance | JsonOutputParser()</code><br/>'
                           'We pipe the prompt template directly into the LLM and bind <code>JsonOutputParser</code> for strict <b>Output Validation</b>. Every agent produces structured JSON, ensuring downstream services never choke on unstructured text.<br/><br/>'
                           'For <b>Tool Definitions and Agent Execution</b>, look at <code>trial_balance.py</code>. Notice our hybrid design: before the agent ever calls an LLM, it executes deterministic domain tools—validating that Debits equal Credits, verifying the core accounting equation, and checking abnormal account signs. It then packages those quantitative findings and feeds them into the LangChain chain for senior auditor commentary.<br/><br/>'
                           'For <b>Workflow Orchestration</b>, I built a 4-stage execution state machine in <code>workflow_engine.py</code>:<br/>'
                           '• <b>Stage 1 (Parallel)</b>: Entity Data Validation—Trial Balance, Variance, and Cash Flow run concurrently per company.<br/>'
                           '• <b>Stage 2 (Sequential)</b>: Deep Dives—Accruals, ASC 606 Revenue Recognition, and Expense categorization.<br/>'
                           '• <b>Stage 3 (Cross-Company)</b>: Intercompany Elimination, matching bilateral transactions across portfolio pairs.<br/>'
                           '• <b>Stage 4 (Group Rollup)</b>: Multi-entity Consolidation and executive ReportLab PDF generation."', script_speech_style))

    # Segment 4
    story.append(Paragraph("[2:30 - 3:30] Criterion 4: Live Execution & Empirical Results", h2_style))
    story.append(Paragraph("[ACTION: Switch to Chrome browser on right. Click 'Run Full Close'. Watch progress bars update live. Then switch to VS Code BENCHMARK_REPORT.md.]", script_action_style))
    story.append(Paragraph('"Let’s watch this run live. When I trigger \'Run Full Close\' on our Next.js dashboard, FastAPI dispatches the orchestrator workflow. Notice the real-time event updates streaming in over Socket.IO WebSockets.<br/><br/>'
                           'The agents are publishing their state transitions into Redis shared memory. If an intercompany mismatch occurs between TechForge SaaS and RetailCo, the Intercompany Agent flags the imbalance, writes the elimination journal to Redis, and automatically triggers an alert email via Resend to the operating partners.<br/><br/>'
                           'Now let\'s look at the <b>actual empirical benchmark results</b> from running this across all 8 operating entities:<br/>'
                           '1. <b>78.3% Reduction in Manual Audit Review</b>: Out of 1,602 total month-end audit items—across 269 trial balance rows, variance thresholds, and 1,008 accrual lines—our agents auto-cleared 1,255 balanced items, flagging only 347 true anomalies for human review. That reduced routine checklist reviews by nearly three quarters!<br/>'
                           '2. <b>53.1% Token Reduction</b>: Naively passing raw CSV ledger tables to downstream agents burned 26,174 tokens per cycle. By implementing Redis shared memory, upstream agents cache structured summaries with a 1-hour TTL. Downstream synthesis agents only read pre-aggregated JSON, slashing pipeline token consumption down to 12,269 tokens."', script_speech_style))

    # Segment 5
    story.append(Paragraph("[3:30 - 4:15] Criterion 5: Technical Problems Encountered & How I Debugged Them", h2_style))
    story.append(Paragraph("[ACTION: Highlight base.py line 111 (SharedMemory) and lines 297-315 (try/except failover loop).]", script_action_style))
    story.append(Paragraph('"During development, I hit two major technical hurdles:<br/><br/>'
                           '<b>Challenge 1: Upstream Context Explosion & Cost</b>. Initially, the Consolidation and Reporting agents ingested raw transaction logs from all 8 companies. The prompt size easily exceeded 25,000 tokens, degrading LLM reasoning accuracy and spiking latency.<br/>'
                           '<i>Fix:</i> I decoupled data ingestion from LLM reasoning using Redis. Upstream agents process raw SQL rows deterministically, compute type totals, and write a compacted JSON payload to Redis. Downstream agents ingest only that summary, cutting token costs by 53%.<br/><br/>'
                           '<b>Challenge 2: LLM API Rate Limits and 429 Cascades</b>. When running 10 agents concurrently across 8 entities, we hit API rate limits on primary LLM providers.<br/>'
                           '<i>Fix:</i> I engineered a resilient fallback cascade in <code>call_llm()</code>. If Claude hits a 429 quota exhaustion, it catches the exception and immediately falls over to OpenAI, then Gemini, then Groq LLaMA-3.3, and finally a deterministic rule-based engine. This eliminated workflow aborts, achieving 100% pipeline reliability."', script_speech_style))

    # Segment 6
    story.append(Paragraph("[4:15 - 5:00] Criterion 6: Scaling to 20× Productivity with Multi-Agent Parallel Development", h2_style))
    story.append(Paragraph("[ACTION: Switch back to Chrome dashboard overview or high-level architecture diagram in docs/ARCHITECTURE.md.]", script_action_style))
    story.append(Paragraph('"Finally, how would we scale our own engineering velocity by 20× using multi-agent parallel development?<br/><br/>'
                           'In traditional software engineering, developers build agents sequentially. But because we established a strict contract in <code>BaseAgent</code> and a declarative database schema:<br/>'
                           '1. <b>Parallel Agent Generation</b>: We can deploy specialized coding agents working in parallel isolated git worktrees. One AI agent implements the SAP ERP connector, another builds the fixed asset depreciation agent, and a third generates unit tests against synthetic ledger fixtures.<br/>'
                           '2. <b>Automated Red-Teaming</b>: An adversary agent injects out-of-balance debits, unearned revenue timing errors, and circular intercompany transactions into the staging DB, verifying whether our domain agents catch 100% of anomalies.<br/><br/>'
                           'By treating software development as an orchestrated multi-agent pipeline—just like month-end closing—a single engineer can oversee what used to take an entire engineering squad.<br/><br/>'
                           'That is FinFlow AI: deterministic precision, multi-agent LangChain orchestration, and real private equity impact. Thank you!"', script_speech_style))

    story.append(Spacer(1, 10))

    # SECTION 4: Code File Reference Table
    story.append(Paragraph("4. Key Code Files & Specific Lines to Reference", h1_style))
    
    code_ref_data = [
        [
            Paragraph("<b>File & Path</b>", table_header_style),
            Paragraph("<b>Lines</b>", table_header_style),
            Paragraph("<b>LangChain / Architectural Mechanism</b>", table_header_style),
        ],
        [
            Paragraph("<code>backend/app/agents/base.py</code>", table_cell_bold),
            Paragraph("L52-109", table_cell_style),
            Paragraph("<b>LLM Initialization:</b> Dynamic provider list (Anthropic, OpenAI, Gemini, Groq).", table_cell_style),
        ],
        [
            Paragraph("<code>backend/app/agents/base.py</code>", table_cell_bold),
            Paragraph("L111-157", table_cell_style),
            Paragraph("<b>Redis Shared Memory:</b> TTL caching (3600s) and event pub/sub mechanism.", table_cell_style),
        ],
        [
            Paragraph("<code>backend/app/agents/base.py</code>", table_cell_bold),
            Paragraph("L284-315", table_cell_style),
            Paragraph("<b>LCEL & Error Handling:</b> <code>ChatPromptTemplate</code> | <code>llm</code> | <code>JsonOutputParser()</code> with failover loop.", table_cell_style),
        ],
        [
            Paragraph("<code>backend/app/agents/trial_balance.py</code>", table_cell_bold),
            Paragraph("L45-80", table_cell_style),
            Paragraph("<b>Deterministic Tools:</b> Debits=Credits validation, abnormal balance identification before LLM invocation.", table_cell_style),
        ],
        [
            Paragraph("<code>backend/app/agents/intercompany.py</code>", table_cell_bold),
            Paragraph("L45-95", table_cell_style),
            Paragraph("<b>Cross-Company Elimination:</b> Bilateral transaction matching matrix & automated journal entry generation.", table_cell_style),
        ],
        [
            Paragraph("<code>backend/app/services/workflow_engine.py</code>", table_cell_bold),
            Paragraph("L38-64", table_cell_style),
            Paragraph("<b>Orchestration DAG:</b> 4-stage execution groups (Validation, Verification, Cross-Company, Consolidation).", table_cell_style),
        ],
        [
            Paragraph("<code>BENCHMARK_REPORT.md</code>", table_cell_bold),
            Paragraph("L18-46", table_cell_style),
            Paragraph("<b>Empirical Verification:</b> 1,602 item benchmark table showing 78.3% auto-clear and 53.1% token savings.", table_cell_style),
        ],
    ]
    t_code = Table(code_ref_data, colWidths=[160, 52, 320])
    t_code.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(primary)),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_code)
    story.append(Spacer(1, 12))

    # SECTION 5: Technical Follow-Up Q&A
    story.append(Paragraph("5. Technical Follow-Up Q&A (Vizuara Defense Coaching)", h1_style))
    
    qa_list = [
        ("Q1: Why did you use standard LCEL and procedural execution groups rather than a dynamic graph like LangGraph?",
         "Accounting month-end close follows a strictly audited, deterministic DAG defined by GAAP/IFRS controls: you cannot execute Consolidation before Intercompany eliminations are booked, and you cannot run variance checks on an unbalanced Trial Balance. Dynamic routing in financial audits introduces compliance risks. Procedural groups backed by Redis shared memory guarantee deterministic step dependencies, audit trails, and idempotent task recovery."),
        
        ("Q2: How do you guarantee the system doesn't hallucinate calculations in financial statements?",
         "LLMs in FinFlow AI are never used for arithmetic. All math is performed by deterministic Python functions in the agent's execute method—such as calculating trial balance differences, comparing variances against 10% / $50,000 thresholds, and netting bilateral intercompany pairs. The LLM is strictly used for cognitive reasoning: assessing business risk, drafting auditor commentary, interpreting ASC 606 revenue timing, and formatting journal entries into validated JSON."),
        
        ("Q3: How does Redis Shared Memory achieve a 53% token reduction?",
         "In a naive multi-agent architecture, downstream agents (Consolidation, Reporting) receive raw ledger tables across all 8 companies, blowing out prompt sizes beyond 25,000 tokens. In FinFlow AI, upstream validation agents write pre-aggregated, structured JSON summaries to Redis with a 1-hour TTL. Downstream agents only ingest the cached summary, dropping downstream prompt ingestion from 14,574 to 669 tokens—a 53.1% overall pipeline token reduction."),
         
        ("Q4: How does your system handle LLM provider rate limits or API outages?",
         "We implemented an automatic provider fallback cascade in BaseAgent.call_llm(). The engine attempts Anthropic Claude first; if rate-limited (HTTP 429) or timed out, it catches the error and fails over seamlessly to OpenAI GPT-4o, Google Gemini Flash, and Groq LLaMA-3.3, finally falling back to a deterministic rule engine. In simulated testing, this eliminated workflow aborts completely.")
    ]

    for q, a in qa_list:
        story.append(Paragraph(f"<b>{q}</b>", h2_style))
        story.append(Paragraph(a, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    build_pdf()
