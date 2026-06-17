# Local & Offline Document Intelligence Tools for Open WebUI

This repository contains a suite of custom **Open WebUI Tools** designed to implement high-fidelity "Chat with Docs" capabilities completely offline and local, bypassing the limitations of traditional vector-based RAG. It also includes native integration with **SharePoint** folders (either locally synced or cloud-hosted via Microsoft Graph API).

---

## Features

1.  **Tabular Inaccuracy Resolution (Excel & CSV):** 
    Uses a local Python Pandas execution tool to run exact mathematical queries, aggregations, and multi-sheet summaries directly on spreadsheets, ensuring 100% computational accuracy.
2.  **Layout-Preserving Document Parsing:** 
    Parses `.pdf`, `.docx`, and `.pptx` documents locally and offline using structures from `pdfplumber`, `python-docx`, and `python-pptx` to preserve tables and structural flow in Markdown.
3.  **Local OCR (Scanned Files):** 
    Uses local Tesseract OCR to read text from scanned images and layouts without cloud api calls.
4.  **Granular User Permissions:** 
    Includes an `AUTHORIZED_EMAILS` Valve configuration inside the SharePoint tool to restrict access to designated user email addresses.

---

## Directory Structure

```
├── README.md
├── open_webui_document_intelligence_guide.md  # Detailed setup and blueprint manual
├── test_local_parser.py                       # Offline test script to verify parser outputs
└── open_webui_tools/
    ├── local_document_parser.py               # Main layout-aware offline parsing engine
    ├── spreadsheet_query.py                   # Custom tool for executing Pandas on Excel/CSV
    ├── pdf_page_renderer.py                   # Converts visual PDF pages to images for vision LLMs
    └── sharepoint_connector.py                # SharePoint directory connector with user filters
```

---

## Installation & Setup

Please refer to [open_webui_document_intelligence_guide.md](open_webui_document_intelligence_guide.md) for detailed step-by-step instructions.

### System Prerequisites
Ensure you install the Tesseract OCR engine on your host machine/container for visual text processing:
*   **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
*   **macOS:** `brew install tesseract`

---

## Verification
You can programmatically test all parsers on your local machine by executing the verification test script:
```bash
python3 test_local_parser.py
```
This generates dummy mock files (spreadsheets, agreements, presentations) and parses them locally to demonstrate exact output formatting.
