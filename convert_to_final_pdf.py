import markdown
from xhtml2pdf import pisa
import os

# Define paths
md_path = os.path.join("docs", "supporting_docs.md")
pdf_path = "Queue_Cure_2026_Supporting_Docs_Final.pdf"

# Read Markdown file
with open(md_path, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert Markdown to HTML with extensions
html_content = markdown.markdown(
    md_content,
    extensions=[
        "tables",
        "fenced_code",
        "nl2br"
    ]
)

# Add page breaks before each major section
html_content = html_content.replace('<h1>Socket Event Diagram</h1>', '<div class="section-start"><h1>Socket Event Diagram</h1>')
html_content = html_content.replace('<h1>Thought Process</h1>', '</div><div class="section-start"><h1>Thought Process</h1>')
html_content = html_content.replace('<h1>API Documentation</h1>', '</div><div class="section-start"><h1>API Documentation</h1>')
html_content = html_content.replace('<h1>Test Cases</h1>', '</div><div class="section-start"><h1>Test Cases</h1>')
html_content = html_content.replace('<h1>Deployment Guide</h1>', '</div><div class="section-start"><h1>Deployment Guide</h1>')
html_content += '</div>'  # Close last section

# Add professional styling and all requirements
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Queue Cure 2026 - Supporting Documentation</title>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm;
            @frame footer {{
                -pdf-frame-content: footerContent;
                bottom: 1cm;
                left: 1cm;
                right: 1cm;
                height: 1.5cm;
            }}
        }}
        body {{
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #000000;
        }}
        /* Cover Page */
        .cover-page {{
            text-align: center;
            padding-top: 8cm;
            page-break-after: always;
        }}
        .cover-page h1 {{
            font-size: 28pt;
            color: #1e3a8a;
            border: none;
            margin-bottom: 0.5cm;
        }}
        .cover-page h2 {{
            font-size: 18pt;
            color: #4f46e5;
            margin-bottom: 0.3cm;
            border: none;
        }}
        .cover-page p {{
            font-size: 13pt;
            margin: 0.3cm 0;
        }}
        /* TOC */
        .toc {{
            page-break-after: always;
        }}
        .toc h2 {{
            border: none;
            margin-bottom: 0.8cm;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 0.4cm 0;
        }}
        .toc a {{
            color: #1e3a8a;
            text-decoration: none;
        }}
        /* Headings */
        h1 {{
            font-size: 24pt;
            color: #1e3a8a;
            border-bottom: 3px solid #1e3a8a;
            padding-bottom: 0.3cm;
            margin-top: 0;
            margin-bottom: 0.8cm;
        }}
        h2 {{
            font-size: 18pt;
            color: #4f46e5;
            margin-top: 1cm;
            margin-bottom: 0.5cm;
            page-break-after: avoid;
        }}
        h3 {{
            font-size: 15pt;
            color: #374151;
            margin-top: 0.7cm;
            margin-bottom: 0.3cm;
            page-break-after: avoid;
        }}
        /* Page Breaks for Major Sections */
        .section-start {{
            page-break-before: always;
        }}
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0.6cm 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.4cm;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background-color: #f3f4f6;
            font-weight: bold;
        }}
        /* Code Blocks */
        pre {{
            background: #1f2937;
            color: #f9fafb;
            padding: 0.5cm;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 10pt;
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            page-break-inside: avoid;
        }}
        code {{
            background: #e5e7eb;
            padding: 0.1cm 0.3cm;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 10pt;
        }}
        /* Lists */
        ul, ol {{
            margin-left: 0.5cm;
            padding-left: 0.5cm;
        }}
        li {{
            margin: 0.2cm 0;
        }}
        /* Diagrams */
        .diagram {{
            text-align: center;
            font-family: 'Courier New', Courier, monospace;
            font-size: 10pt;
            background: #f9fafb;
            padding: 0.5cm;
            border-radius: 5px;
            margin: 0.6cm 0;
            white-space: pre-wrap;
            page-break-inside: avoid;
        }}
        /* Footer */
        #footerContent {{
            text-align: center;
            font-size: 10pt;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
            padding-top: 0.3cm;
        }}
    </style>
</head>
<body>
    <!-- Cover Page -->
    <div class="cover-page">
        <h1>Queue Cure 2026</h1>
        <h2>Supporting Documentation</h2>
        <p><strong>Real-Time Clinic Queue Management System</strong></p>
        <p>Flask • Socket.IO • SQLite • Bootstrap 5</p>
        <p style="margin-top: 1.5cm; font-weight: bold;">Hackathon Submission</p>
    </div>

    <!-- Table of Contents -->
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            <li><a href="#socket-event-diagram">Socket Event Diagram</a></li>
            <li><a href="#thought-process">Thought Process</a></li>
            <li><a href="#api-documentation">API Documentation</a></li>
            <li><a href="#test-cases">Test Cases</a></li>
            <li><a href="#deployment-guide">Deployment Guide</a></li>
        </ul>
    </div>

    <!-- Content -->
    {html_content}

    <!-- Footer -->
    <div id="footerContent">
        Queue Cure 2026 | Supporting Documentation | Hackathon Submission | Page <pdf:pagenumber> of <pdf:pagecount>
    </div>
</body>
</html>
"""

# Fix diagram styling (wrap <pre> elements with .diagram class)
full_html = full_html.replace('<pre>', '<div class="diagram"><pre>')
full_html = full_html.replace('</pre>', '</pre></div>')

# Convert HTML to PDF
with open(pdf_path, "wb") as output_file:
    pisa.CreatePDF(
        full_html,
        dest=output_file,
        encoding='utf-8'
    )

print("Final PDF generated successfully:", os.path.abspath(pdf_path))
print("Check the PDF for all requirements!")
print("Estimated pages: ~8-10 pages")
