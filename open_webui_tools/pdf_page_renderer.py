"""
title: PDF Visual Page Renderer
author: Advanced Agentic RAG Team
version: 1.1.0
description: Renders pages of a PDF locally as images. Invoke ONLY when the user explicitly asks to visually inspect charts, maps, blueprints, or scanned sections of a PDF. Do NOT use for greetings or generic text queries.
requirements: pymupdf, pillow
"""

import os
import glob
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

class Tools:
    class Valves(BaseModel):
        SHAREPOINT_LOCAL_PATH: str = Field(
            default="/media/hirthikbalaji/AGPT DATA/SAMPLE",
            description="Absolute path to your synced SharePoint or OneDrive folder containing local PDFs."
        )

    def __init__(self):
        self.valves = self.Valves()

    def render_pdf_pages(self, filename: str, start_page: int = 1, end_page: int = 1) -> str:
        """
        Converts pages of a PDF file into Base64 PNG images. Use this ONLY when you need to visually check drawings, tables, or scanned page designs.
        
        :param filename: Name of the PDF file (e.g. 'report.pdf').
        :param start_page: Starting page number (1-indexed).
        :param end_page: Ending page number (1-indexed, inclusive).
        :return: Base64 data URLs of the rendered pages or an error message.
        """
        filepath = self._resolve_path(filename)
        if not filepath:
            return f"Error: File '{filename}' not found in the SharePoint directory."
            
        try:
            doc = fitz.open(filepath)
            total_pages = len(doc)
            
            # Constrain pages
            start = max(1, start_page) - 1
            end = min(total_pages, end_page)
            
            if start >= total_pages:
                return f"Error: Start page {start_page} exceeds total pages ({total_pages})."
                
            results = []
            for page_num in range(start, end):
                page = doc.load_page(page_num)
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                results.append(f"--- Page {page_num + 1} Visual Representation ---\n"
                               f"data:image/png;base64,{img_str}\n")
                               
            return "\n".join(results)
        except Exception as e:
            return f"Error rendering PDF pages: {str(e)}"

    def _resolve_path(self, filename: str) -> str:
        local_path = self.valves.SHAREPOINT_LOCAL_PATH.strip().strip('"').strip("'")
        if not local_path or not os.path.exists(local_path):
            return None
            
        full_path = os.path.join(local_path, filename)
        if os.path.exists(full_path):
            return full_path
            
        # Recursive glob search inside SharePoint folder
        matches = glob.glob(os.path.join(local_path, "**", filename), recursive=True)
        if matches:
            return matches[0]
            
        matches_glob = glob.glob(os.path.join(local_path, "**", f"*{filename}*"), recursive=True)
        if matches_glob:
            return matches_glob[0]
            
        return None
