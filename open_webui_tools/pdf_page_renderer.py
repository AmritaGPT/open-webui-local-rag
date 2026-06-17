"""
title: PDF Visual Page Renderer
author: Advanced Agentic RAG Team
version: 1.0.0
description: Renders pages of a PDF as high-resolution images. Essential for analyzing scanned documents, layout-heavy PDFs, charts, and presentations visually using Vision LLMs.
requirements: pymupdf, pillow
"""

import os
from typing import Dict, List, Any
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

class Tools:
    def __init__(self):
        pass

    def render_pdf_pages(self, filename: str, start_page: int = 1, end_page: int = 1) -> str:
        """
        Renders specified pages of a PDF document into Base64-encoded PNG images.
        Use this when a document is scanned, contains complex layout charts, or visual elements, allowing you to "see" the exact page.
        
        :param filename: Name of the PDF file (e.g., 'scanned_report.pdf').
        :param start_page: Starting page number (1-indexed).
        :param end_page: Ending page number (1-indexed, inclusive).
        :return: Base64 data URLs of the rendered pages or an error message.
        """
        search_paths = [
            "/app/backend/data/uploads",
            "/mnt/uploads",
            "./backend/data/uploads",
            ".",
        ]
        
        filepath = None
        for path in search_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                filepath = full_path
                break
                
        if not filepath:
            return f"Error: File '{filename}' not found."
            
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
                # Render page to a pixmap (300 DPI for high quality)
                zoom = 300 / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Compress and encode to base64
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                results.append(f"--- Page {page_num + 1} Visual Representation ---\n"
                               f"data:image/png;base64,{img_str}\n")
                               
            return "\n".join(results)
        except Exception as e:
            return f"Error rendering PDF pages: {str(e)}"
