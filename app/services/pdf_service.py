from fpdf import FPDF

#--------------------------- Function for formatting PDF ---------------------------
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Placify - Personalized Career Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, 0, 1, 'L', True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        # Ensure unicode characters don't crash FPDF (basic handling)
        body = str(body).encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, body)
        self.ln(3)

#--------------------------- Function for generating PDF ---------------------------
def generate_pdf(data, filename="report.pdf"):
    pdf = PDFReport()
    pdf.add_page()

    # Introduction
    pdf.chapter_title(f"Assessment Mode: {data.get('mode', 'Unknown').capitalize()}")
    pdf.chapter_body(f"Candidate: {data.get('candidate_name', 'Student')}")
    pdf.chapter_body(f"Readiness Score: {data.get('readiness_score')}%")
    
    # Strengths
    pdf.chapter_title("Key Strengths")
    strengths_text = "\n".join([f"- {s}" for s in data.get('strengths', [])])
    if strengths_text:
        pdf.chapter_body(strengths_text)

    # Gaps
    pdf.chapter_title("Areas for Improvement")
    gaps_text = "\n".join([f"- {g}" for g in data.get('gaps', [])])
    if gaps_text:
        pdf.chapter_body(gaps_text)

    # Action Plan
    pdf.chapter_title("Action Plan")
    plan_text = "\n".join([f"{i+1}. {p}" for i, p in enumerate(data.get('action_plan', []))])
    if plan_text:
        pdf.chapter_body(plan_text)

    # Jobs
    pdf.chapter_title("Recommended Jobs")
    for job in data.get('job_recommendations', []):
        pdf.chapter_body(f"Role: {job.get('role', 'N/A')}\nCompany: {job.get('company', 'N/A')}\nLocation: {job.get('location', 'Remote/TBD')}\nMatch: {job.get('match', '')}")
        pdf.ln(2)

    # Return PDF as bytes (no filesystem write)
    raw = pdf.output(dest='S')
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    return raw.encode('latin-1')
