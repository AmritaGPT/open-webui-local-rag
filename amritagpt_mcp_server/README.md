# AmritaGPT Document Intelligence MCP Server

This directory contains a **Model Context Protocol (MCP)** server that exposes local layout-aware document search, full-text parsing, OCR, and spreadsheet analytical execution capabilities. 

By running this as an MCP server, you decouple the heavy python dependencies (`pandas`, `fitz`, `pdfplumber`, etc.) from your AI clients, running them in an isolated process on your computer.

---

## Capabilities

The MCP server exposes the following tools:
1.  `list_all_documents`: Recursive catalog list of all files in the synced folder.
2.  `search_documents`: Offline filename search and recursive keyword full-text search inside PDFs, Word files, and text documents.
3.  `read_and_parse_document`: Layout-aware structural parser for PDF, Word, PowerPoint, and local OCR for scanned images.
4.  `get_spreadsheet_schema`: Inspect sheets, column headers, and data types in Excel and CSV files.
5.  `query_spreadsheet`: Execute calculations on sheets using Pandas code.
6.  `render_pdf_page_as_image`: Renders specific PDF pages into Base64 PNGs for visual inspection.

---

## Local Directory Path
By default, the server is configured to look strictly inside:
`/media/hirthikbalaji/AGPT DATA/SAMPLE`

If you need to change this path, open `mcp_server.py` and modify the `DEFAULT_PATH` variable at the top of the script.

---

## Installation & Running

### Step 1: Install Dependencies
Create a virtual environment (recommended) and install the requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
*(Make sure `tesseract-ocr` is installed on your computer: `sudo apt install tesseract-ocr` on Linux).*

### Step 2: Run the Server
You can run the server directly using standard Python or via `uv` (recommended):
```bash
# Using Python directly (in your venv)
python3 mcp_server.py

# Or using uv (no virtual environment creation needed)
uv run mcp_server.py
```
By default, running `python3 mcp_server.py` starts the server in stdio mode (ready to receive JSON-RPC messages from Cursor/Claude).

---

## Integration Guides

### Integration with Open WebUI (SSE Mode)
To connect the server to your running Open WebUI container or host:

1.  **Run with an SSE (Server-Sent Events) Transport:**
    Open WebUI connects to MCP servers over HTTP/SSE. You can run the MCP server using `mcp dev` or a micro-framework wrapper to expose it as an HTTP service:
    ```bash
    mcp dev mcp_server.py --port 8000
    ```
2.  **Configure in Open WebUI:**
    *   Navigate to **Admin Panel > Settings > Connections > MCP Servers** in the Open WebUI browser dashboard.
    *   Add a new connection:
        *   **Name:** `AmritaGPT Docs`
        *   **Type:** `sse`
        *   **URL:** `http://localhost:8000/sse` (or the corresponding container hostname/port).
    *   Click **Submit**.

### Integration with Claude Desktop (Stdio Mode)
Add the following configuration block to your Claude Desktop config file (located at `~/.config/Claude/claude_desktop_config.json` on Linux/macOS):

```json
{
  "mcpServers": {
    "amritagpt-doc-intel": {
      "command": "python3",
      "args": [
        "/home/hirthikbalaji/AGPT_FE/Brain/amritagpt_mcp_server/mcp_server.py"
      ],
      "env": {
        "PATH": "/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

### Integration with Cursor IDE
1.  Open **Cursor Settings > Features > MCP**.
2.  Click **+ Add New MCP Server**.
3.  Fill in the details:
    *   **Name:** `AmritaGPT`
    *   **Type:** `command`
    *   **Command:** `python3 /home/hirthikbalaji/AGPT_FE/Brain/amritagpt_mcp_server/mcp_server.py`
4.  Click **Save**. The green status indicator will show connection confirmation.
