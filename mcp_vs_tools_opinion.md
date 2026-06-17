# Technical Evaluation: Model Context Protocol (MCP) vs. Open WebUI Workspace Tools

**To:** Project Incharge / Development Team  
**Subject:** Architectural Comparison and Recommendations for MCP Integration  

---

## 1. Executive Summary & Recommendation
For an enterprise-grade document intelligence system accessing sensitive SharePoint data, **transitioning to a Model Context Protocol (MCP) server is the highly recommended long-term architecture.**

While **Open WebUI Workspace Tools** are excellent for quick prototyping and single-user environments, they run in-process with the main Open WebUI application, creating security risks, package dependency conflicts, and scaling bottlenecks. **MCP** decouples the data parsers and analytical tools into an isolated, secure microservice that can be audited independently and reused across multiple AI clients (such as Cursor, Claude Desktop, and LibreChat).

---

## 2. Side-by-Side Comparison

| Feature | Open WebUI Tools (Current) | MCP Server (Proposed) | Winner |
| :--- | :--- | :--- | :---: |
| **Process Isolation** | **None.** Runs directly inside the Open WebUI backend process. A crash in a tool can crash the WebUI. | **Full.** Runs as a separate microservice. Open WebUI communicates via secure JSON-RPC. | **MCP** |
| **Security & Auditing** | Tool code has full access to the host's filesystem and environment variables. Hard to sandbox. | Strict interface boundaries. The MCP server only exposes designated functions/directories. | **MCP** |
| **Dependency Management** | Heavy libraries (`pandas`, `openpyxl`, `pdfplumber`, `pytesseract`) must be installed in the WebUI host/Docker. | Dependencies are isolated to the MCP container/venv. Open WebUI stays lightweight. | **MCP** |
| **Cross-Platform Reusability**| Locked into Open WebUI's custom ecosystem. | Standardized protocol. The same server works with Cursor, Windsurf, or Claude Desktop. | **MCP** |
| **Setup Complexity** | **Very Low.** Copy-paste python scripts into the web interface. | **Medium.** Requires running a background process or container (Stdio or SSE). | **Tools** |

---

## 3. Detailed Architectural Trade-Offs

### Why Workspace Tools are Good (For Small Scale)
*   **Simple deployment:** There is no server to run. The code is saved directly in the database of Open WebUI.
*   **Low latency:** Run directly in the local process space, saving network overhead.

### Why MCP is Better for Production Teams
1.  **Cleaner Docker Setup:** Open WebUI containers are often run read-only or in strict environments where installing custom native binaries (like `tesseract-ocr`) on the fly is restricted or volatile. An MCP server runs as a separate container containing all necessary binary dependencies.
2.  **No Package Conflicts:** Installing data science libraries (like `pandas` or `fitz`) inside the Open WebUI environment can sometimes cause package conflicts with the WebUI's internal dependencies (like `pydantic` versions).
3.  **Role-Based File Security:** The MCP server can run under a restricted host system user that only has read permissions to the `/media/hirthikbalaji/AGPT DATA/SAMPLE` directory, preventing the AI from accidentally accessing other parts of the server's drive.

---

## 4. Proposed MCP Server Blueprint (Python-MCP SDK)

If you decide to migrate, the four tools we developed can be combined into a single local Python MCP Server. Below is the blueprint code for the server:

```python
# mcp_server.py
# Run using: pip install mcp[cli]
from mcp.server.fastmcp import FastMCP
import os
import glob
import pandas as pd
import pdfplumber
import docx
from pptx import Presentation

# Initialize FastMCP Server
mcp = FastMCP("AmritaGPT-Doc-Intelligence")

SHAREPOINT_PATH = "/media/hirthikbalaji/AGPT DATA/SAMPLE"

@mcp.tool()
def search_documents(query: str) -> str:
    """
    Search synced SharePoint directory for files matching keywords.
    """
    if not os.path.exists(SHAREPOINT_PATH):
        return f"Error: Local path '{SHAREPOINT_PATH}' does not exist."
    
    search_pattern = os.path.join(SHAREPOINT_PATH, "**", f"*{query}*")
    matches = glob.glob(search_pattern, recursive=True)
    if not matches:
        return "No documents found."
        
    results = [f"- {os.path.basename(f)} ({os.path.getsize(f)/1024:.1f} KB)" for f in matches[:10]]
    return "\n".join(results)

@mcp.tool()
def parse_document(filename: str) -> str:
    """
    Parses PDF, Word, or PPTX files layout-aware locally.
    """
    filepath = os.path.join(SHAREPOINT_PATH, filename)
    if not os.path.exists(filepath):
        return "File not found."
        
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        output = []
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                output.append(f"## Page {i+1}\n" + (page.extract_text() or ""))
        return "\n".join(output)
    # (Word and PPTX parser logic fits here...)
    return "Unsupported format."

@mcp.tool()
def query_spreadsheet(filename: str, code: str) -> str:
    """
    Runs local pandas analytical calculations on spreadsheets.
    """
    filepath = os.path.join(SHAREPOINT_PATH, filename)
    if not os.path.exists(filepath):
        return "File not found."
    df = pd.read_excel(filepath) if filename.endswith('.xlsx') else pd.read_csv(filepath)
    local_vars = {'df': df, 'result': None}
    exec(code, {}, local_vars)
    return str(local_vars.get('result', "Error: 'result' not set."))

if __name__ == "__main__":
    mcp.run()
```

### How to connect Open WebUI to the MCP Server:
1.  Run the MCP server locally (e.g. as a background systemd service or inside a dedicated Docker container).
2.  Open **Admin Panel > Settings > Connections > MCP Servers** in Open WebUI.
3.  Add a new server with type `stdio` (if on the same host machine) or `sse` (if running as a separate HTTP service), and specify the command path or endpoint.
