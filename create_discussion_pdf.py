import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
        
        primary_color = colors.HexColor("#0f172a")
        muted_text = colors.HexColor("#64748b")
        border_color = colors.HexColor("#e2e8f0")
        
        page_width, page_height = letter
        
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(primary_color)
            self.drawString(54, page_height - 36, "FINFLOW AI  |  ENTRY-LEVEL (SDE < 1 YR) RESUME GUIDE")
            
            self.setFont("Helvetica", 8)
            self.setFillColor(muted_text)
            self.drawRightString(page_width - 54, page_height - 36, "AI NATIVE & SWE ROLES")
            
            self.setStrokeColor(border_color)
            self.setLineWidth(0.5)
            self.line(54, page_height - 42, page_width - 54, page_height - 42)

        self.setStrokeColor(border_color)
        self.setLineWidth(0.5)
        self.line(54, 45, page_width - 54, 45)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(muted_text)
        self.drawString(54, 30, "CONFIDENTIAL — PREPARED FOR ENTRY-LEVEL (SDE-1) RESUME PREPARATION")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_width - 54, 30, page_str)
        
        self.restoreState()


def build_pdf(filename="FinFlow_AI_Resume_Discussion_Summary.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=16
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f8fafc"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=10
    )

    story = []
    
    story.append(Paragraph("FinFlow AI — Entry-Level Resume Guide (< 1 Yr Exp)", title_style))
    story.append(Paragraph("Realistic, Non-Senior Tone for Junior SWE (SDE-1) & Junior AI Builder", subtitle_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Tone & Style Philosophy for SDE < 1 Year Experience", h1_style))
    story.append(Paragraph(
        "Overly senior jargon like <i>'Architected enterprise microservices'</i> or <i>'Designed system topologies'</i> raises red flags for entry-level applicants. For candidate SDEs with &lt; 1 year of experience, resume points focus on standard, believable development tasks: <b>Building endpoints, writing agent workflows, setting up caches, creating UI components, and containerizing services.</b>",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Software Engineer LaTeX Block (Entry-Level / SDE-1)", h1_style))
    
    swe_latex = r"""{\textbf{FinFlow AI} \hfill 
{\small \textit{Python \textbar{} FastAPI \textbar{} Next.js \textbar{} PostgreSQL \textbar{} Redis \textbar{} Docker}} 
{\textbar{}\highlightlink{https://github.com/amitk2003/Multimodal-Agentic-ai}{Code} \textbar{} \highlightlink{https://multimodal-agentic-ai.vercel.app/}{Live}}
\begin{itemize}
\item Built RESTful and WebSocket API endpoints to process financial data across 8 portfolio companies (\$615M+ revenue), \textbf{reducing manual close turnaround time by 80\%}.
\item Implemented real-time data caching and pub/sub messaging to pass execution updates, achieving \textbf{sub-second latency} for live event notifications.
\item Developed a responsive dashboard UI with interactive charts and error-tracking components to monitor \textbf{10 automated agent workflow streams}.
\item Created automated PDF report generation scripts and containerized application services using \textbf{Docker} for smooth cloud deployment.
\end{itemize}}"""

    story.append(Preformatted(swe_latex, code_style))
    story.append(Spacer(1, 8))

    story.append(PageBreak())
    story.append(Paragraph("3. AI Native Builder LaTeX Block (Entry-Level / Junior AI Builder)", h1_style))

    ai_latex = r"""{\textbf{FinFlow AI} \hfill 
{\small \textit{Python \textbar{} LangChain \textbar{} Multi-LLM \textbar{} Redis \textbar{} FastAPI \textbar{} Docker}} 
{\textbar{}\highlightlink{https://github.com/amitk2003/Multimodal-Agentic-ai}{Code} \textbar{} \highlightlink{https://multimodal-agentic-ai.vercel.app/}{Live}}
\begin{itemize}
\item Developed a multi-agent system with 10 specialized agents to handle trial balance checks, revenue recognition rules, and intercompany eliminations across operating entities.
\item Implemented an automated API fallback handler across multiple LLM providers to handle rate limits and \textbf{prevent job failures during run execution}.
\item Built custom evaluation prompts and agents to detect debit/credit mismatches, stale accruals, and transaction errors, \textbf{reducing manual audit reviews by 75\%}.
\item Integrated a shared memory layer using Redis to pass context between agents, \textbf{cutting redundant token consumption by 30\%} across execution pipelines.
\end{itemize}}"""

    story.append(Preformatted(ai_latex, code_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("4. Entry-Level Interview Strategy", h1_style))
    
    qa_data = [
        ["Interview Question", "Entry-Level Authentic Answer"],
        ["What was your role in this project?", "I built the full-stack system from scratch using FastAPI and Next.js. I wrote the agent handlers in LangChain, connected Redis for pub/sub messaging, and created the PDF generator."],
        ["How did you handle LLM API rate limits?", "I wrote a try-except fallback function in Python that checks if Gemini or Claude returns a rate limit error, and automatically switches the call to Groq or OpenAI."],
        ["How did you test your multi-agent flow?", "I seeded sample portfolio financial data into PostgreSQL via FastAPI endpoints and triggered agent runs via WebSockets to test execution output in the dashboard."]
    ]
    
    qa_table_data = []
    for row in qa_data:
        qa_table_data.append([
            Paragraph(f"<b>{row[0]}</b>", ParagraphStyle('QCol', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor("#0f172a"))),
            Paragraph(row[1], ParagraphStyle('ACol', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor("#334155")))
        ])
        
    t_qa = Table(qa_table_data, colWidths=[2.2*inch, 4.4*inch])
    t_qa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(t_qa)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    build_pdf()
