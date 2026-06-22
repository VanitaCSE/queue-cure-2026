import markdown
from xhtml2pdf import pisa
import os

# Define paths
md_path = os.path.join("docs", "supporting_docs.md")
pdf_path = "Queue_Cure_2026_Supporting_Docs.pdf"

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

# Add professional styling
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Queue Cure 2026 - Hackathon Supporting Docs</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        body {{
            font-family: Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.6;
        }}
        h1 {{
            color: #1e3a8a;
            border-bottom: 3px solid #1e3a8a;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #4f46e5;
            margin-top: 25px;
        }}
        h3 {{
            color: #374151;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f3f4f6;
            font-weight: bold;
        }}
        pre {{
            background: #1f2937;
            color: #f9fafb;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 10pt;
        }}
        code {{
            background: #e5e7eb;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            border: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏥 Queue Cure 2026</h1>
        <h3>Hackathon Supporting Documentation</h3>
    </div>
    {html_content}
</body>
</html>
"""

# Convert HTML to PDF
with open(pdf_path, "wb") as output_file:
    pisa.CreatePDF(
        full_html,
        dest=output_file,
        encoding='utf-8'
    )

print(f"✅ PDF generated successfully: {os.path.abspath(pdf_path)}")
