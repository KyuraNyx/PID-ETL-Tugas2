#!/usr/bin/env python3
"""Convert DOCX to pristine styled PDF using Mammoth + WeasyPrint"""

import os
import mammoth
from weasyprint import HTML, CSS

docx_path = 'Tugas2_ETL_245150301111027_Hayqal Husein Alhabsyi.docx'
pdf_target_1 = 'Tugas2_ETL_245150301111027_Hayqal Husein Alhabsyi.pdf'
pdf_target_2 = '245150301111027_Hayqal Husein Alhabsyi_Tugas 2_ ETL_PID (1).pdf'

print(f"📖 Reading {docx_path}...")
with open(docx_path, 'rb') as docx_file:
    result = mammoth.convert_to_html(docx_file)
    html_content = result.value
    messages = result.messages

css_styling = """
@page {
    size: A4;
    margin: 2.5cm 2.0cm 2.5cm 2.5cm;
    @bottom-center {
        content: counter(page);
        font-family: 'Liberation Sans', 'DejaVu Sans', Arial, sans-serif;
        font-size: 9pt;
        color: #666;
    }
}

body {
    font-family: 'Liberation Sans', 'DejaVu Sans', 'Helvetica Neue', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #222;
    text-align: justify;
}

h1 {
    color: #1A5376;
    font-size: 18pt;
    border-bottom: 2px solid #2E4057;
    padding-bottom: 4px;
    margin-top: 24pt;
    margin-bottom: 12pt;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    color: #2E4057;
    font-size: 13.5pt;
    margin-top: 16pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
}

h3 {
    color: #1A5376;
    font-size: 11.5pt;
    margin-top: 12pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
}

p {
    margin-top: 0;
    margin-bottom: 6pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 9pt;
    page-break-inside: avoid;
}

th {
    background-color: #2E4057;
    color: #ffffff;
    font-weight: bold;
    padding: 6pt 8pt;
    border: 1px solid #1A2838;
    text-align: left;
}

td {
    padding: 5pt 8pt;
    border: 1px solid #D0D8E0;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #F8FAFC;
}

pre, code {
    font-family: 'DejaVu Sans Mono', 'Liberation Mono', 'Courier New', monospace;
    font-size: 8.5pt;
}

pre {
    background-color: #F4F7F9;
    border: 1px solid #D1DDE5;
    border-left: 4px solid #1A5376;
    padding: 8pt 10pt;
    margin: 8pt 0;
    white-space: pre-wrap;
    word-break: break-all;
    page-break-inside: avoid;
    line-height: 1.35;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 14pt auto;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
}

blockquote {
    background-color: #EBF4FA;
    border-left: 4px solid #2E4057;
    padding: 8pt 12pt;
    margin: 10pt 0;
    font-style: italic;
}
"""

full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <title>Tugas 2 ETL Sensor Data dengan Pandas - 245150301111027 Hayqal Husein Alhabsyi</title>
</head>
<body>
{html_content}
</body>
</html>"""

print("🎨 Rendering PDF via WeasyPrint...")
html_obj = HTML(string=full_html, base_url='.')
css_obj = CSS(string=css_styling)

html_obj.write_pdf(pdf_target_1, stylesheets=[css_obj])
print(f"✅ Generated: {pdf_target_1} ({os.path.getsize(pdf_target_1):,} bytes)")

html_obj.write_pdf(pdf_target_2, stylesheets=[css_obj])
print(f"✅ Generated: {pdf_target_2} ({os.path.getsize(pdf_target_2):,} bytes)")
