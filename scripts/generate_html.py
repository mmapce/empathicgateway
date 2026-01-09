#!/usr/bin/env python3
"""
Convert PROJECT_REPORT.md to HTML for browser PDF export
"""
import markdown2
from pathlib import Path

# Read markdown
md_content = Path("PROJECT_REPORT.md").read_text()

# Convert to HTML
html_content = markdown2.markdown(
    md_content,
    extras=["tables", "fenced-code-blocks", "header-ids"]
)

# Add CSS styling
css_style = """
<style>
    @page {
        size: A4;
        margin: 2cm;
    }
    @media print {
        h1 {
            page-break-before: always;
        }
        h1:first-of-type {
            page-break-before: avoid;
        }
    }
    body {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        margin-top: 40px;
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
    <h1 style="text-align: center; border: none;">EmpathicGateway</h1>
    <h2 style="text-align: center; border: none;">AI-Powered Priority Routing & PII Detection System</h2>
    <p style="text-align: center; font-style: italic;">Proje Raporu</p>
    <hr>
    {html_content}
</body>
</html>
"""

# Save HTML
Path("PROJECT_REPORT.html").write_text(full_html)
print("✅ HTML created: PROJECT_REPORT.html")
print("\n📄 PDF oluşturmak için:")
print("1. PROJECT_REPORT.html dosyasını tarayıcıda açın")
print("2. Cmd+P (Print) tuşuna basın")
print("3. 'Save as PDF' seçin")
print("4. PROJECT_REPORT.pdf olarak kaydedin")
