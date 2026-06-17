# Analysis of Issues and Limitations in Traditional RAG Systems

This document outlines the core technical challenges and failure points experienced when using traditional Retrieval-Augmented Generation (RAG) pipelines (chunking and vector database indexing) for diverse corporate documents. These limitations directly motivated our transition to the local hybrid layout-aware and code-interpreting architecture.

---

## 1. Tabular Data Destruction (Excel & CSV Files)
Traditional RAG indexes spreadsheets by converting rows into plain text strings (e.g., `"Row 1: Product A, Units 10, Price 5.00"`) and generating vector embeddings.
*   **Loss of Contextual Grid Structure:** The spatial boundaries of column-row relationships are flattened. If a vector database splits a spreadsheet into arbitrary text chunks, the column headers are separated from the rows below them, making the lower rows completely uninterpretable by the LLM.
*   **Inability to Perform Mathematical Operations:** LLMs cannot do math over retrieved text chunks. If a user asks *"What is the total revenue of products in the Electronics category?"*, a vector search will return random rows containing "Electronics". The LLM is forced to guess or manually add the numbers, leading to severe hallucination. It cannot perform aggregations, filtering, joins, or sorting.
*   **Worksheet Fragmentation:** Excels with multiple worksheets are indexed as separate files. Traditional RAG cannot coordinate joins across sheets (e.g. matching a `Product_ID` on "Sheet 1" with sales transactions on "Sheet 2").

---

## 2. Loss of Document Layout Geometry (Word & PDF Files)
Standard text extraction models (e.g., raw PDF/Word loaders) strip away all page formatting to feed raw text strings to embedding models.
*   **Jumbled Multi-Column Layouts:** For documents formatted in multiple columns (like newspapers, academic papers, or corporate summaries), basic loaders read text from left-to-right across the entire page, stitching lines from Column A to Column B together. This results in gibberish.
*   **Table Degradation:** Tables inside PDFs or Word documents are converted into strings where cell contents are merged without boundaries (e.g., `"Item Cost Qty Cloud 100 2"` instead of a grid). The LLM cannot identify which value belongs to which header.
*   **Header and Outline Loss:** Stripping font sizes and heading weights makes it impossible for the LLM to understand document hierarchy, causing it to treat footers, headers, page numbers, and major chapter titles with equal semantic weight.

---

## 3. Spatial Context Fragmentation (PowerPoint Presentations)
Slides are highly visual structures where layout dictates context. Information is distributed across distinct shapes, text boxes, and side-by-side tables.
*   **Sequential Text Dumps:** PowerPoint text extractors dump slide shapes in the order they were added to the slide, rather than their visual reading order. This disrupts the narrative flow.
*   **Slide Chunking Splits:** If a slide's content spans a chunk boundary, part of the slide's points are indexed in Chunk A and the rest in Chunk B. The LLM can never retrieve the complete visual context of that slide in a single query.

---

## 4. Visual Blindness (Scanned Documents & Diagrams)
Standard vectorization pipelines fail completely on visual-heavy or non-digital media.
*   **Skipped Content:** Scanned PDFs (which are essentially page images) are uploaded as empty text objects. They are indexed as blank documents, completely hiding their contents from the RAG search.
*   **Lack of Diagrammatic Interpretation:** Graphs, flowchart diagrams, architecture designs, and annotations are completely omitted from text extraction, leaving the LLM blind to visual summaries.

---

## 5. Security & Offline Compliance Violations
To fix layout issues, standard systems often rely on external proprietary cloud APIs (such as Adobe PDF Extract or cloud-hosted layout extraction models).
*   **Data Leakage:** Uploading sensitive corporate files (like client agreements, HR rosters, or proprietary designs) to external cloud servers for processing violates internal security compliance and data sovereignty policies.
