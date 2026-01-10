#!/usr/bin/env python3
"""
Convert PROJECT_REPORT.md to PDF using markdown2 and weasyprint
"""

import markdown2
from weasyprint import HTML, CSS
from pathlib import Path

# Read markdown
md_content = Path("PROJECT_REPORT.md").read_text()

# Convert to HTML
html_content = markdown2.markdown(
    md_content, extras=["tables", "fenced-code-blocks", "header-ids", "toc"]
)

# Add CSS styling
css_style = """
<style>
    @page {
        size: A4;
        margin: 2.5cm;
    }
    body {
        font-family: 'Arial', sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        page-break-before: always;
    }
    h1:first-of-type {
        page-break-before: avoid;
    }
    h2 {
        color: #34495e;
        border-bottom: 2px solid #95a5a6;
        padding-bottom: 5px;
        margin-top: 30px;
    }
    h3 {
        color: #7f8c8d;
        margin-top: 20px;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        overflow-x: auto;
        font-size: 9pt;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        font-size: 10pt;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 15px;
        margin: 20px 0;
        font-style: italic;
        color: #555;
    }
    a {
        color: #3498db;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .page-break {
        page-break-after: always;
    }
</style>
"""

# Combine HTML
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>EmpathicGateway Project Report</title>
    {css_style}
</head>
<body>
    {html_content}
</body>
</html>
"""

# Generate PDF
print("Generating PDF...")
HTML(string=full_html).write_pdf("PROJECT_REPORT.pdf")
print("✅ PDF created: PROJECT_REPORT.pdf")
