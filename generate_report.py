import os
import sys
from datetime import datetime

# Import ReportLab modules
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display the total page count.
    Adds a professional header and footer with page numbers.
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
        # We don't draw headers/footers on the cover page (Page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        
        # Color Palette
        primary_color = colors.HexColor("#1e293b")  # Dark slate
        accent_color = colors.HexColor("#4f46e5")   # Indigo
        muted_text = colors.HexColor("#64748b")     # Cool grey
        border_color = colors.HexColor("#e2e8f0")   # Light grey border
        
        # Page size
        page_width, page_height = letter
        
        # --- Draw Header ---
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(primary_color)
        self.drawString(54, page_height - 36, "APEX CAPITAL PARTNERS  |  TECHNICAL ARCHITECTURE BRIEF")
        
        self.setFont("Helvetica", 8)
        self.setFillColor(muted_text)
        self.drawRightString(page_width - 54, page_height - 36, "MONTH-END CLOSE ORCHESTRATOR")
        
        # Header thin rule
        self.setStrokeColor(border_color)
        self.setLineWidth(0.75)
        self.line(54, page_height - 42, page_width - 54, page_height - 42)
        
        # --- Draw Footer ---
        # Footer thin rule
        self.line(54, 50, page_width - 54, 50)
        
        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(muted_text)
        self.drawString(54, 36, "Confidential - For Internal Engineering Use Only")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_width - 54, 36, page_text)
        
        self.restoreState()

def create_report_pdf(output_path):
    # Setup document
    # Margins: 0.75 in (54 pt) on all sides. Top margin leaves room for header (offset at 42).
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=60
    )
    
    styles = getSampleStyleSheet()
    
    # --- Custom Typography / Styles ---
    primary_color = colors.HexColor("#1e293b")
    accent_color = colors.HexColor("#4f46e5")
    dark_grey = colors.HexColor("#334155")
    light_bg = colors.HexColor("#f8fafc")
    table_border = colors.HexColor("#cbd5e1")
    
    # Modify existing styles to avoid conflicts
    styles['Normal'].textColor = dark_grey
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    
    # Define new styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=primary_color,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=30
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748b")
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceBefore=22,
        spaceAfter=12,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'ReportBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#0f172a")
    )

    story = []
    
    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 1.5 * inch))
    
    # Decorative Accent Bar
    accent_bar_data = [['']]
    accent_bar_table = Table(accent_bar_data, colWidths=[100], rowHeights=[6])
    accent_bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), accent_color),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(accent_bar_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Month-End Close Orchestrator", title_style))
    story.append(Paragraph("Deep-Dive Architectural & Full-Stack Analysis", ParagraphStyle('CoverSubTitle2', parent=title_style, fontSize=18, leading=22, textColor=colors.HexColor("#475569"))))
    story.append(Paragraph("A Developer's Blueprint: Multi-Agent Coordination, Redis Shared Memory, WebSockets, and Scale Pathing", subtitle_style))
    
    story.append(Spacer(1, 2.5 * inch))
    
    # Metadata Block
    date_str = datetime.now().strftime("%B %d, %Y")
    metadata_text = f"""
    <b>Prepared For:</b> Apex Capital Partners &bull; Financial Technology Group<br/>
    <b>Author:</b> Principal AI Engineer<br/>
    <b>Date:</b> {date_str}<br/>
    <b>Version:</b> 1.0.0 (Production Blueprint)<br/>
    <b>Status:</b> Approved for Implementation
    """
    story.append(Paragraph(metadata_text, meta_style))
    
    story.append(PageBreak())
    
    # =========================================================================
    # SECTION 1: ORCHESTRATOR MANAGEMENT & MULTI-AGENT COORDINATION
    # =========================================================================
    story.append(Paragraph("1. Orchestrator Management & Multi-Agent Coordination", h1_style))
    story.append(Paragraph(
        "The Month-End Close Orchestrator uses a <i>hybrid coordinator-worker</i> design. "
        "Rather than having a single massive script check every financial statement, the system splits "
        "responsibilities among 9 specialized agent classes. The <b>Orchestrator Agent</b> acts as the supervisor, "
        "controlling the execution path, tracking progress, handling errors, and generating summaries.",
        body_style
    ))
    
    story.append(Paragraph("How the Orchestrator Coordinates Other Agents", h2_style))
    story.append(Paragraph(
        "The Orchestrator coordinates agent tasks by utilizing a structured <b>Workflow Engine</b> state machine. "
        "Instead of running agents randomly, the system schedules them in 4 distinct sequential <i>Execution Groups</i>. "
        "This ensures that dependee data is fully processed before downstream agents run:",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>1. Stage 1: Validation & Analysis (Parallel, Per-Company):</b> "
        "The <i>Trial Balance Validator</i>, <i>Variance Analysis</i>, and <i>Cash Flow Reconciliation</i> agents are triggered "
        "simultaneously for all companies. They validate data integrity and identify gross discrepancies.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>2. Stage 2: Verification (Sequential, Per-Company):</b> "
        "The <i>Accrual Verification</i>, <i>Revenue Recognition</i>, and <i>Expense Categorization</i> agents process "
        "each company's accounts. These agents depend on clean baseline numbers established in Stage 1.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>3. Stage 3: Cross-Company (Sequential, Global):</b> "
        "The <i>Intercompany Elimination</i> agent runs globally across all companies. It matches buy-sell "
        "transactions between sister entities and suggests elimination entries.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>4. Stage 4: Group Rollup & Reporting (Sequential, Global):</b> "
        "The <i>Consolidation Agent</i> combines all individual ledgers (applying the intercompany eliminations), "
        "and the <i>Reporting Communication Agent</i> creates the final monthly briefing deck and sends emails.",
        bullet_style
    ))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Workflow State Machine Mechanics", h2_style))
    story.append(Paragraph(
        "The coordination is driven programmatically in the database using two main SQLAlchemy tables:<br/>"
        "&bull; <b>WorkflowRun:</b> Tracks the overall close process for a period (e.g., '2026-01'), including status (pending, running, completed, failed) and progress percentage.<br/>"
        "&bull; <b>AgentTask:</b> Tracks the status of a specific agent running for a specific company (e.g., 'variance_analysis' for 'retailco').<br/><br/>"
        "The background loop in <code>main.py</code> queries the <code>WorkflowEngine</code> for the next available tasks. "
        "The engine only returns tasks whose execution group priority matches the current active stage. When all tasks in a group "
        "finish (status becomes 'completed' or 'failed'), the engine automatically moves to the next priority level.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # =========================================================================
    # SECTION 2: THE ROLE OF REDIS & CELERY IN THE PROJECT
    # =========================================================================
    story.append(Paragraph("2. The Role of Redis & Celery", h1_style))
    story.append(Paragraph(
        "A critical question in this architecture is how background tasks and inter-agent memory are handled. "
        "Let's look at how Redis is actually used and what role Celery plays in the current codebase.",
        body_style
    ))
    
    story.append(Paragraph("How Redis is Actually Used", h2_style))
    story.append(Paragraph(
        "Redis plays two distinct, active roles in this project: <b>Shared Memory</b> and <b>Event Publishing (Pub/Sub)</b>.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>1. Inter-Agent Shared Memory:</b> "
        "Agents must share information. For example, the <i>Consolidation Agent</i> needs to know the eliminations created by "
        "the <i>Intercompany Agent</i>. Since agents execute independently, they store and retrieve data in Redis using the "
        "<code>SharedMemory</code> class wrapper (found in <code>base.py</code>). Stored objects use a standard key format:<br/>"
        "<code>agent:{{agent_type}}:{{company_id_or_all}}:{{period}}</code> (e.g., <code>agent:variance_analysis:retailco:2026-01</code>). "
        "This data has a default Time-To-Live (TTL) of 1 hour, acting as a fast cache. If Redis is down, the class "
        "gracefully falls back to an in-memory Python dictionary.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>2. Event Publishing (Pub/Sub):</b> "
        "When an agent completes a run, it publishes a JSON payload to the <code>agent_events</code> Redis channel, "
        "notifying downstream listeners of the state change. It also publishes live UI messages to the <code>ws_broadcast</code> channel "
        "to trigger real-time updates.",
        body_style
    ))
    
    # Callout Box for Celery Analysis
    celery_text = """
    <b>CRITICAL ANALYSIS: The Celery Misconception</b><br/>
    While <code>celery[redis]</code> is declared in <code>requirements.txt</code>, and a <code>REDIS_CELERY_URL</code> env variable is defined, <b>Celery is NOT actually used in the current codebase</b>.<br/><br/>
    The system is coordinated using an <code>asyncio</code> background loop (called <code>autonomous_scheduler</code> in <code>main.py</code>) that wakes up every 30 seconds, checks the PostgreSQL database for pending tasks, and executes them inline using Python's asyncio runtime.
    """
    
    callout_data = [[Paragraph(celery_text, callout_style)]]
    callout_table = Table(callout_data, colWidths=[doc.width])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fee2e2")), # Light red tint
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fca5a5")),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(Spacer(1, 10))
    story.append(callout_table)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("What happens if Celery is removed?", h2_style))
    story.append(Paragraph(
        "If you remove Celery from the project dependencies right now, <b>absolutely nothing happens to the active system</b>. "
        "The application will launch and run perfectly because the current scheduling is fully handled by internal FastAPI "
        "asyncio tasks polling the Postgres DB. There are no active Celery workers, celery tasks, or Celery configurations "
        "imported in the application. You can safely remove it from <code>requirements.txt</code> without breaking current functionality.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # =========================================================================
    # SECTION 3: SYSTEM SCALABILITY
    # =========================================================================
    story.append(Paragraph("3. How to Make the System Scalable", h1_style))
    story.append(Paragraph(
        "The current setup runs all agents in the same process as the FastAPI web server. "
        "While this works great for a demo with 8 small companies, it will fail in production "
        "with hundreds of companies or large financial datasets because LLM calls are slow and block CPU/network resources. "
        "To make the system enterprise-ready, we must scale multiple layers:",
        body_style
    ))
    
    # Scalability Table
    scale_headers = ["Layer", "Current Approach", "Production Scale Solution"]
    scale_rows = [
        [Paragraph("<b>Task Queue</b>", body_style), 
         Paragraph("Inline <code>asyncio</code> background loop polling database.", body_style), 
         Paragraph("<b>True Celery workers</b>. Offload agent execution to a pool of distributed worker containers running on ECS or Kubernetes.", body_style)],
        [Paragraph("<b>Memory Layer</b>", body_style), 
         Paragraph("Single Redis instance (DB 0) with a dictionary fallback.", body_style), 
         Paragraph("<b>Redis Cluster</b> with master-replica replication to guarantee shared memory availability and persist agent states.", body_style)],
        [Paragraph("<b>Database</b>", body_style), 
         Paragraph("Single PostgreSQL instance with no indexes or partitioning.", body_style), 
         Paragraph("Add <b>Read Replicas</b> for API queries. Partition financial tables (like <code>TrialBalanceLine</code>) by <code>period</code>. Index <code>company_id</code>.", body_style)],
        [Paragraph("<b>LLM Calls</b>", body_style), 
         Paragraph("Sequential direct API calls to Claude/OpenAI.", body_style), 
         Paragraph("Implement <b>Anthropic Prompt Caching</b> to reduce costs. Use a queue-based rate limiter (like RabbitMQ) to prevent API rate limit (TPM/RPM) errors.", body_style)],
        [Paragraph("<b>Data Loading</b>", body_style), 
         Paragraph("Pandas reads entire CSV files directly into memory.", body_style), 
         Paragraph("Stream files from <b>AWS S3</b> in chunks or use bulk copy commands (<code>COPY FROM</code>) for loading million-row ledgers quickly.", body_style)]
    ]
    
    table_data = [scale_headers] + scale_rows
    # Doc width is 504 pt (8.5 * 72 - 108)
    scale_table = Table(table_data, colWidths=[1.1*inch, 2.3*inch, 3.6*inch])
    scale_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, table_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, light_bg]),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
    ]))
    story.append(scale_table)
    story.append(Spacer(1, 15))
    
    # =========================================================================
    # SECTION 4: AI ENGINEER'S INSIGHTS ON MULTI-AGENT SOLUTIONS
    # =========================================================================
    story.append(Paragraph("4. AI Engineer's Insights on Multi-Agent Implementation", h1_style))
    story.append(Paragraph(
        "Implementing a multi-agent system in a high-stakes domain like corporate finance requires moving beyond basic LLM prompts. "
        "Here are the core principles that guide my decisions as an AI engineer:",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>1. Build Rigid Sandbox Boundaries for LLMs:</b> "
        "LLMs are creative but notoriously bad at precision arithmetic. Never let the LLM do the math. "
        "Instead, the Python code should perform the calculations (e.g., subtracting debits from credits, calculating variance percentages) "
        "and feed the structured results to the LLM. The LLM's job is solely <i>cognitive</i>: reading the variance numbers and explaining "
        "why they occurred based on accounting guidelines.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "<b>2. Error Isolation (Fail-Safe Execution):</b> "
        "If the <i>Revenue Recognition Agent</i> fails because of an LLM timeout, the entire monthly close process "
        "for other companies should not crash. Design agents to be fully self-contained. "
        "A failure in one agent should write a failure status and error details to the DB, issue an alert, and allow "
        "independent tasks to proceed.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "<b>3. Strict Output Structure via JSON Parsers:</b> "
        "Downstream agents and frontend components rely on structured data. We use LangChain's <code>JsonOutputParser</code> "
        "to force LLMs to respond in JSON. We must also supply robust fallback mock generators if the LLM output is malformed, "
        "preventing runtime type errors.",
        bullet_style
    ))
    
    story.append(PageBreak())
    
    # =========================================================================
    # SECTION 5: FRONTEND SEED DATA & BACKEND CASCADE FLOW
    # =========================================================================
    story.append(Paragraph("5. End-to-End Walkthrough: Seeding & Live Updates", h1_style))
    story.append(Paragraph(
        "Let's trace exactly what happens under the hood when a user clicks the <b>Seed Data</b> button on the dashboard.",
        body_style
    ))
    
    story.append(Paragraph("Step 1: Frontend Interaction", h2_style))
    story.append(Paragraph(
        "In <code>frontend/src/app/page.tsx</code>, clicking the 'Seed Data' button calls the async function <code>handleSeedData()</code>. "
        "This function updates the UI state (setting <code>isSeeding = true</code> to show a loading spinner) and fires an HTTP POST request "
        "to the backend API endpoint: <code>/api/seed</code>.",
        body_style
    ))
    
    story.append(Paragraph("Step 2: Backend REST Endpoint Reception", h2_style))
    story.append(Paragraph(
        "The FastAPI server in <code>app/main.py</code> intercepts this POST request at the <code>@app.post(\"/api/seed\")</code> router. "
        "It opens a database session (<code>SessionLocal()</code>) and instantiates the <code>DataLoader</code> class, passing the session.",
        body_style
    ))
    
    story.append(Paragraph("Step 3: Database Deletion & Cascading (Clear Phase)", h2_style))
    story.append(Paragraph(
        "To avoid duplicate entries, the backend calls <code>loader.clear_all()</code>. This executes SQL <code>DELETE</code> statements "
        "in a specific sequence to respect database foreign key constraints. The deletion cascade proceeds from child tables to parent tables:<br/>"
        "<code>Report &rarr; Notification &rarr; AgentLog &rarr; AgentTask &rarr; WorkflowRun &rarr; AccrualSchedule &rarr; BankStatement &rarr; IntercompanyTransaction &rarr; Budget &rarr; TrialBalanceLine &rarr; Company</code>.<br/>"
        "A database commit is made, leaving a completely blank slate.",
        body_style
    ))
    
    story.append(Paragraph("Step 4: Parsing & Inserting (Load Phase)", h2_style))
    story.append(Paragraph(
        "The backend calls <code>loader.load_all()</code>, which reads clean sample datasets from the file system:<br/>"
        "&bull; It reads <code>company_metadata.json</code> to load the 8 companies.<br/>"
        "&bull; It loops through the <code>trial_balances/</code>, <code>prior_year/</code>, <code>budgets/</code>, <code>intercompany/</code>, "
        "<code>bank_statements/</code>, and <code>accrual_schedules/</code> directories.<br/>"
        "&bull; It parses the CSVs using <b>Pandas DataFrames</b>, iterates through the rows, maps them to SQLAlchemy models, and adds them "
        "to the session. Finally, it commits the changes to PostgreSQL.",
        body_style
    ))
    
    story.append(Paragraph("Step 5: Frontend Reload & WebSocket Updates", h2_style))
    story.append(Paragraph(
        "The FastAPI server returns a success response. The frontend receives this response, sets <code>hasData = true</code>, and triggers "
        "a page reload (<code>window.location.reload()</code>). The refreshed page fetches the newly seeded database state via GET requests.<br/><br/>"
        "<b>How WebSockets are used during agent runs:</b><br/>"
        "WebSockets provide live, sub-second progress updates during agent runs so the user isn't stuck staring at static pages. "
        "FastAPI initializes a <code>socketio.AsyncServer</code>. When the React client mounts, it establishes a persistent connection. "
        "When an agent runs, it calls <code>self._broadcast(message)</code>, which publishes the update to Redis and emits an <code>agent_update</code> event. "
        "The React hook <code>useWebSocket.ts</code> catches this event and immediately updates the state, showing the active agent's status "
        "and activity logs in the UI feed without requiring manual page refreshes.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # =========================================================================
    # SECTION 6: EVERY AGENT'S WORK STEP-BY-STEP (SIMPLE LANGUAGE)
    # =========================================================================
    story.append(Paragraph("6. Step-by-Step Guide: What Every Agent Actually Does", h1_style))
    story.append(Paragraph(
        "Let's demystify what each of the 9 specialized agents does. Instead of complex terms, "
        "here is exactly what they do in plain English:",
        body_style
    ))
    
    agent_info = [
        ("1. Trial Balance Validator", "This agent checks if the books are mathematically sound. It ensures that total debits equal total credits, flagging any initial entry errors before any analytical work begins."),
        ("2. Variance Analysis Agent", "Think of this as the comparison checker. It compares this month's actual spending/earnings against both the planned budget and last year's actual numbers. If an account has a major jump (like spending 50% more than budgeted), it flags it."),
        ("3. Cash Flow Reconciler", "This agent acts as the bank auditor. It compares the company's internal bookkeeping ledger against the actual bank statements, line-by-line, to ensure all cash coming in and going out is recorded and matches."),
        ("4. Accrual Verification Agent", "This agent ensures that adjustments are made for future or past events. It checks schedules for prepaid expenses, depreciation, and interest to confirm that these adjustments are booked in the correct month."),
        ("5. Revenue Recognition Agent", "This agent verifies the company's earnings rules. It checks if the company is recording revenue correctly based on performance rules (e.g. ASC 606), preventing companies from claiming future money as current earnings."),
        ("6. Expense Categorization Agent", "This agent scans transactions to find out-of-place expenses. It flags if a software invoice is accidentally filed under 'marketing travel' or if there are anomalous payments to unapproved vendors."),
        ("7. Intercompany Agent", "This agent acts as the cross-company referee. When sister companies sell to or buy from each other, this agent makes sure Entity A's recorded receivable matches Entity B's recorded payable, generating matching entries to wipe them out on consolidation."),
        ("8. Consolidation Agent", "This agent is the aggregator. It takes the individual sheets from all 8 companies, applies the intercompany elimination entries, converts currencies if necessary, and rolls them up into a single consolidated portfolio sheet."),
        ("9. Reporting Agent", "This agent is the communicator. It compiles all findings, drafts the final monthly executive report, packages key charts, and emails the summary dashboard link to the private equity managers.")
    ]
    
    for title, desc in agent_info:
        story.append(Paragraph(f"<b>{title}</b>", h2_style))
        story.append(Paragraph(desc, body_style))
    
    story.append(PageBreak())
    
    # =========================================================================
    # SECTION 7: FULL-STACK SOLUTION DESIGN THINKING
    # =========================================================================
    story.append(Paragraph("7. Full-Stack Solution Design Thinking", h1_style))
    story.append(Paragraph(
        "To build a successful multi-agent solution, an AI engineer must trace the problem "
        "from initial user pain points to a deployed full-stack system using structured <b>Design Thinking</b>:",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>1. Empathize: Understanding the User Pain</b><br/>"
        "Month-end close in private equity and corporate accounting is notoriously stressful. Financial controllers "
        "spend days manually cross-checking hundreds of Excel sheets, searching for typos, reconciling intercompany entries, "
        "and chasing discrepancies. They are exhausted, prone to oversight, and get reporting packages out weeks late.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>2. Define: Outlining the Core Problems</b><br/>"
        "We defined the core problems to solve:<br/>"
        "&bull; <i>Data fragmentation:</i> Ledger lines, bank statements, and budgets live in separate siloed tables.<br/>"
        "&bull; <i>Sequential delays:</i> Accountants can't perform consolidation until intercompany entries match.<br/>"
        "&bull; <i>Explainability:</i> Standard automated rule engines say 'error' but cannot explain *why* or suggest corrections.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>3. Ideate: Designing the Multi-Agent Concept</b><br/>"
        "Instead of a monolithic program, we ideated a virtual accounting team. Each agent simulates a human specialist. "
        "We designed a shared-memory model (Redis) so the agents could pass context, simulating a team passing files "
        "around a table. The Orchestrator manages the workflow states.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>4. Prototype & Build: Developing the Technical Stack</b><br/>"
        "We built a functional full-stack prototype:<br/>"
        "&bull; <b>Database (PostgreSQL + SQLAlchemy):</b> Stores relational financial data, tasks, and audit logs.<br/>"
        "&bull; <b>Backend API (FastAPI + Asyncio):</b> Provides high-performance async REST routes and Socket.IO endpoints.<br/>"
        "&bull; <b>AI Engine (LangChain + Claude):</b> Uses LLM chains to analyze complex transactions and write explanations.<br/>"
        "&bull; <b>Memory & Pub/Sub (Redis):</b> Shares state and broadcasts execution events.<br/>"
        "&bull; <b>Frontend (Next.js + Socket.IO-client):</b> Renders a live visual dashboard showing agent progress.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>5. Test & Verify: Operational Testing</b><br/>"
        "We verify the solution by running end-to-end tests: seeding the DB, initiating a close workflow, watching the "
        "agents execute Stage 1 to Stage 4 in sequence, and checking that the reporting agent successfully compiles a "
        "consolidated package with zero manual intervention.",
        body_style
    ))
    
    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    output_pdf = "Month_End_Close_Architecture_Analysis.pdf"
    if len(sys.argv) > 1:
        output_pdf = sys.argv[1]
    
    print(f"Generating PDF report at: {output_pdf}")
    create_report_pdf(output_pdf)
    print("PDF generation complete!")
