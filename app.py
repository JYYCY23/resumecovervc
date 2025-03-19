from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.utils import simpleSplit

app = Flask(__name__)

# Define the upload folder and ensure it exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def create_info_pdf(data, filename):
    """Generate a PDF with candidate details in the specified format."""
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    styles = getSampleStyleSheet()

    def draw_header_footer(page_num):
        """Draws the header and footer on each page."""
        # Draw logo
        logo_width, logo_height = 120, 100  # Adjust size as needed
        c.drawImage(logo_path, 510, height - 90, width=logo_width, height=logo_height, preserveAspectRatio=True)

        # Draw header underline
        c.setStrokeColorRGB(0, 0, 0)  # black color
        c.setLineWidth(1)
        c.line(100, height - 60, width - 75, height - 60)

        # Draw footer underline
        c.setStrokeColorRGB(0, 0, 0)  # black color
        c.setLineWidth(1)
        c.line(100, 50, width - 75, 50)
        
        # Footer: Page Number
        c.setFont("Helvetica", 10)  # Set font and size
        c.drawRightString(width - 50, 30, f"Page {page_num}")

    # Start the first page
    page_num = 1
    draw_header_footer(page_num)

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(1, 0, 0)  # Red color
    c.drawCentredString(width / 2, height - 40, "Private & Confidential")
    c.setFillColorRGB(0, 0, 0)  # Reset to black

    y_position = height - 100
    c.setFont("Helvetica-Bold", 12)

    # Fixed X positions for proper alignment
    label_x = 100   # Left align labels
    colon_x = 220   # Fixed column for colons
    value_x = 250   # Start of values

    # Client Info Section
    info_content = [
        ("Client                           :", data['client']),
        ("Candidate name         :", data['candidate_name']),
        ("Position applied         :", data['position_applied']),
    ]

    for label, value in info_content:
        c.drawString(100, y_position, f"{label:<20} {value}")
        y_position -= 20

    # Presented by + Date in the same line
    y_position -= 20
    c.drawString(100, y_position, "Presented by:")
    y_position -= 15
    c.setFont("Helvetica", 10)
    c.drawString(100, y_position, "Jacky You Chiek Yi")
    y_position -= 15
    c.drawString(100, y_position, "Senior Executive Search Consultant")
    y_position -= 15
    c.drawString(100, y_position, "Agensi Pekerjaan Versatile Creation Sdn. Bhd.")
    c.drawRightString(width - 100, y_position, f"Date: {datetime.today().strftime('%d/%m/%Y')}")
    
    y_position -= 30
    c.line(100, y_position + 10, width - 100, y_position + 10)
    y_position -= 30

    # Executive Summary Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y_position, "Executive Summary")
    y_position -= 20

    # Bullet Points for Executive Summary
    c.setFont("Helvetica", 10)
    summary_lines = data['executive_summary'].split('\n')
    for line in summary_lines:
        import textwrap
        wrapped_text = textwrap.wrap(line, width=80)  # Adjust width as needed
        for text in wrapped_text:
            c.drawString(90, y_position, "•")
            c.drawString(105, y_position, text)
            y_position -= 15
            if y_position < 50:  # Prevent text from going out of bounds
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = height - 50

    # Candidate Details with Aligned Colons
    details = [
        ("Age", data['age']),
        ("Current salary", data['current_salary']),
        ("Expected salary", data['expected_salary']),
        ("Notice period", data['notice_period']),
        ("Reason of leaving", data['reason_leaving']),
    ]

    y_position -= 20
    for label, value in details:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(100, y_position, f"{label}:")
        c.setFont("Helvetica", 10)
        c.drawString(250, y_position, value)
        y_position -= 20
        if y_position < 50:  # Ensure content stays within page limits
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = height - 50

    c.save()
    return pdf_path

def merge_pdfs(info_pdf, resume_pdf, output_pdf):
    """Merge two PDFs into one."""
    pdf_writer = PdfWriter()
    
    # Add info PDF pages
    info_reader = PdfReader(info_pdf)
    for page in info_reader.pages:
        pdf_writer.add_page(page)
    
    # Add resume PDF pages
    resume_reader = PdfReader(resume_pdf)
    for page in resume_reader.pages:
        pdf_writer.add_page(page)
    
    # Write the output PDF
    with open(output_pdf, 'wb') as out:
        pdf_writer.write(out)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return "No file uploaded", 400

        resume = request.files['resume']
        if resume.filename == '':
            return "No selected file", 400

        data = {
            "client": request.form['client'],
            "candidate_name": request.form['candidate_name'],
            "position_applied": request.form['position_applied'],
            "age": request.form['age'],
            "current_salary": request.form['current_salary'],
            "expected_salary": request.form['expected_salary'],
            "notice_period": request.form['notice_period'],
            "reason_leaving": request.form['reason_leaving'],
            "executive_summary": request.form['executive_summary']
        }

        # Save the uploaded resume
        resume_filename = secure_filename(resume.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
        resume.save(resume_path)

        # Generate the info PDF
        info_pdf = create_info_pdf(data, "candidate_info.pdf")
        
        # Merge the PDFs
        final_pdf = os.path.join(app.config['UPLOAD_FOLDER'], f"{data['candidate_name']}_final.pdf")
        merge_pdfs(info_pdf, resume_path, final_pdf)
        
        # Send the merged PDF as a response
        return send_file(final_pdf, as_attachment=True)
    
    return render_template('index.html')

# Path to your logo image
logo_path = r"C:\Users\Jacky\OneDrive\Desktop\Versatile Creation Master\VC Multimedia\VC Posters\Logo\VC logo without circle jpg.jpg"

if __name__ == '__main__':
    app.run(debug=True)