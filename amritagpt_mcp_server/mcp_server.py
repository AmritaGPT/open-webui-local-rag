"""
AmritaGPT Document Intelligence MCP Server
Author: Advanced Agentic RAG Team
Version: 1.0.0
Description: A Model Context Protocol (MCP) server providing layout-aware document search, 
             retrieval, OCR, and spreadsheet computations locally and offline.
"""

import os
import glob
import time
import base64
import io
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# MCP SDK Import
from mcp.server.fastmcp import FastMCP

# Data Processing Dependencies
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import docx
from pptx import Presentation
from PIL import Image
import pytesseract

# Initialize MCP Server
mcp = FastMCP("AmritaGPT-Doc-Intelligence")

# Default SharePoint Synced Directory
DEFAULT_PATH = "/media/hirthikbalaji/AGPT DATA/SAMPLE"

def _resolve_safe_path(filename: str) -> str:
    """Sanitizes filename and resolves path, preventing directory traversal."""
    sanitized_filename = os.path.basename(filename)
    # Support relative nested paths like "Contracts/NDA.pdf" safely
    if "/" in filename or "\\" in filename:
        clean_parts = [os.path.basename(p) for p in re.split(r'[/\\]', filename) if p and p != '..']
        sanitized_filename = os.path.join(*clean_parts)
        
    full_path = os.path.normpath(os.path.join(DEFAULT_PATH, sanitized_filename))
    if not full_path.startswith(os.path.normpath(DEFAULT_PATH)):
        raise ValueError("Directory traversal attempt blocked.")
    return full_path

@mcp.tool()
def list_all_documents() -> str:
    """
    Lists all documents available in the local repository recursively, showing their relative paths and sizes.
    """
    if not os.path.exists(DEFAULT_PATH):
        return f"Error: Synced repository directory '{DEFAULT_PATH}' does not exist."
        
    search_pattern = os.path.join(DEFAULT_PATH, "**", "*")
    files = glob.glob(search_pattern, recursive=True)
    
    output = ["### Synced Document Repository Listings:\n"]
    file_count = 0
    for filepath in files:
        if os.path.isfile(filepath):
            file_count += 1
            rel_path = os.path.relpath(filepath, DEFAULT_PATH)
            size_kb = os.path.getsize(filepath) / 1024
            mod_time = time.ctime(os.path.getmtime(filepath))
            output.append(f"- **File:** `{rel_path}`\n  - Size: {size_kb:.1f} KB | Last Modified: {mod_time}")
            
    if file_count == 0:
        return "The repository is currently empty."
    return "\n".join(output)

@mcp.tool()
def search_documents(query: str, search_contents: bool = True) -> str:
    """
    Searches the repository for documents matching keywords.
    Can perform filename search and recursive offline full-text content search.
    
    :param query: Keywords to search for (e.g. 'Chennai campus', 'sales matrix').
    :param search_contents: If True, scans text content of PDFs and text files offline for the query term.
    """
    if not os.path.exists(DEFAULT_PATH):
        return "Error: Synced repository directory does not exist."
        
    search_pattern = os.path.join(DEFAULT_PATH, "**", "*")
    all_items = glob.glob(search_pattern, recursive=True)
    
    matches = []
    # 1. Filename matching
    for filepath in all_items:
        if os.path.isfile(filepath):
            filename = os.path.basename(filepath)
            if query.lower() in filename.lower():
                matches.append((filepath, "Filename match"))
                
    # 2. Content search fallback (PDF, DOCX, TXT)
    if search_contents:
        for filepath in all_items:
            if os.path.isfile(filepath) and filepath not in [m[0] for m in matches]:
                ext = os.path.splitext(filepath)[1].lower()
                try:
                    text_content = ""
                    if ext == '.txt':
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            text_content = f.read()
                    elif ext == '.pdf':
                        with pdfplumber.open(filepath) as pdf:
                            # Search first 5 pages quickly
                            text_content = " ".join([page.extract_text() or "" for page in pdf.pages[:5]])
                    elif ext == '.docx':
                        doc = docx.Document(filepath)
                        text_content = " ".join([p.text for p in doc.paragraphs[:20]])
                        
                    if query.lower() in text_content.lower():
                        # Extract snippet
                        match_obj = re.search(rf"([^.?!]*?{re.escape(query)}[^.?!]*?[.?!])", text_content, re.IGNORECASE)
                        snippet = match_obj.group(1).strip() if match_obj else f"Matches found in content."
                        matches.append((filepath, f"Content snippet: \"... {snippet} ...\""))
                except Exception:
                    continue # Skip parsing errors during search
                    
    if not matches:
        return f"No documents or text matches for '{query}' found in repository."
        
    results = [f"### Search Results for '{query}':\n"]
    for idx, (path, match_reason) in enumerate(matches[:10]):
        rel_path = os.path.relpath(path, DEFAULT_PATH)
        results.append(f"{idx+1}. **File:** `{rel_path}`\n   - **Match Reason:** {match_reason}\n   - **Size:** {os.path.getsize(path)/1024:.1f} KB")
        
    return "\n".join(results)

@mcp.tool()
def read_and_parse_document(filename: str) -> str:
    """
    Parses a PDF, Word document (.docx), PowerPoint slide (.pptx), or Scanned Image locally.
    Maintains table structures, headings, and outlines sequentially in Markdown format.
    """
    try:
        filepath = _resolve_safe_path(filename)
    except Exception as e:
        return str(e)
        
    if not os.path.exists(filepath):
        return f"Error: File '{filename}' not found."
        
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.pdf':
            output = []
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    output.append(f"## Page {i + 1}\n")
                    tables = page.extract_tables()
                    if tables:
                        output.append("### Tables Extracted:\n")
                        for table in tables:
                            markdown_table = []
                            for r_idx, row in enumerate(table):
                                clean_row = [str(cell).strip().replace("\n", " ") if cell is not None else "" for cell in row]
                                markdown_table.append("| " + " | ".join(clean_row) + " |")
                                if r_idx == 0:
                                    separator = "| " + " | ".join(["---"] * len(clean_row)) + " |"
                                    markdown_table.append(separator)
                            output.append("\n".join(markdown_table) + "\n\n")
                    text = page.extract_text()
                    if text:
                        output.append("### Text Content:\n" + text + "\n\n")
            return "\n".join(output)
            
        elif ext == '.docx':
            doc = docx.Document(filepath)
            output = []
            for element in doc.element.body:
                if element.tag.endswith('p'):
                    p = docx.text.paragraph.Paragraph(element, doc)
                    if p.text.strip():
                        output.append(p.text + "\n")
                elif element.tag.endswith('tbl'):
                    t = docx.table.Table(element, doc)
                    markdown_table = []
                    for r_idx, row in enumerate(t.rows):
                        row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                        markdown_table.append("| " + " | ".join(row_cells) + " |")
                        if r_idx == 0:
                            separator = "| " + " | ".join(["---"] * len(row_cells)) + " |"
                            markdown_table.append(separator)
                    output.append("\n".join(markdown_table) + "\n\n")
            return "\n".join(output)
            
        elif ext == '.pptx':
            prs = Presentation(filepath)
            output = []
            for i, slide in enumerate(prs.slides):
                output.append(f"## Slide {i + 1}\n")
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        output.append(shape.text.strip() + "\n")
                    if shape.has_table:
                        markdown_table = []
                        for r_idx, row in enumerate(shape.table.rows):
                            row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                            markdown_table.append("| " + " | ".join(row_cells) + " |")
                            if r_idx == 0:
                                separator = "| " + " | ".join(["---"] * len(row_cells)) + " |"
                                markdown_table.append(separator)
                        output.append("\n".join(markdown_table) + "\n\n")
            return "\n".join(output)
            
        elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)
            return f"### OCR Text Output:\n{text}"
        else:
            return f"Unsupported file type '{ext}' for local parsing."
    except Exception as e:
        return f"Error parsing file: {str(e)}"

@mcp.tool()
def get_spreadsheet_schema(filename: str) -> str:
    """
    Examines an Excel or CSV file structure, listing the sheet names, columns, and column data types.
    Always call this first before performing spreadsheet calculations.
    """
    try:
        filepath = _resolve_safe_path(filename)
    except Exception as e:
        return str(e)
        
    if not os.path.exists(filepath):
        return "Spreadsheet file not found."
        
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, nrows=5)
            cols = ", ".join([f"`{col}` ({df[col].dtype})" for col in df.columns])
            return f"**CSV File columns:**\n- {cols}"
        elif filepath.endswith(('.xlsx', '.xls')):
            xl = pd.ExcelFile(filepath)
            sheets = xl.sheet_names
            result = [f"**Excel File contains {len(sheets)} sheet(s):**"]
            for sheet in sheets:
                df = pd.read_excel(filepath, sheet_name=sheet, nrows=5)
                cols = ", ".join([f"`{col}` ({df[col].dtype})" for col in df.columns])
                result.append(f"- **Sheet Name:** `{sheet}`\n  - **Columns:** {cols}")
            return "\n".join(result)
        else:
            return "Unsupported file type."
    except Exception as e:
        return f"Error reading schema: {str(e)}"

@mcp.tool()
def query_spreadsheet(filename: str, code: str) -> str:
    """
    Runs Python Pandas code on a local spreadsheet to execute calculations, filters, or category groups.
    - If spreadsheet has 1 sheet, DataFrame is pre-loaded as 'df'.
    - If spreadsheet has multi-sheets, loaded as dictionary of DataFrames 'sheets' (e.g. sheets['Sheet1']).
    - Assign the final computed value to 'result'.
    """
    try:
        filepath = _resolve_safe_path(filename)
    except Exception as e:
        return str(e)
        
    if not os.path.exists(filepath):
        return "Spreadsheet file not found."
        
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            sheets = {"default": df}
        elif filepath.endswith(('.xlsx', '.xls')):
            sheets = pd.read_excel(filepath, sheet_name=None)
            df = list(sheets.values())[0] if len(sheets) == 1 else None
        else:
            return "Unsupported file format."
    except Exception as e:
        return f"Error loading file: {str(e)}"
        
    local_vars = {
        'sheets': sheets,
        'df': df,
        'pd': pd,
        'result': None
    }
    
    try:
        # Executes code blocks locally
        exec(code, {}, local_vars)
        result = local_vars.get('result')
        if result is None:
            return "Code ran successfully, but 'result' variable was not assigned."
        return str(result)
    except Exception as e:
        return f"Error executing calculation: {str(e)}"

@mcp.tool()
def render_pdf_page_as_image(filename: str, page_num: int = 1) -> str:
    """
    Converts a single PDF page into a base64 PNG data URL.
    Use this when you need to inspect visual charts, logos, diagrams, layouts, or forms.
    """
    try:
        filepath = _resolve_safe_path(filename)
    except Exception as e:
        return str(e)
        
    if not os.path.exists(filepath):
        return "PDF file not found."
        
    try:
        doc = fitz.open(filepath)
        total_pages = len(doc)
        idx = max(1, min(total_pages, page_num)) - 1
        
        page = doc.load_page(idx)
        zoom = 300 / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return f"--- Page {idx + 1} Visual Representation ---\ndata:image/png;base64,{img_str}"
    except Exception as e:
        return f"Error rendering page: {str(e)}"

if __name__ == "__main__":
    mcp.run()
