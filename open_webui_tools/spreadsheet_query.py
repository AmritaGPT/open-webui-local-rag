"""
title: Excel & CSV Spreadsheet Analyzer
author: Advanced Agentic RAG Team
version: 1.0.0
description: Executes Python/Pandas commands on CSV or Excel (.xlsx) files to get precise answers, filtering, and summaries. Avoids vector-database inaccuracies for structured spreadsheets.
requirements: pandas, openpyxl
"""

import os
import glob
from typing import Dict, List, Any
import pandas as pd

class Tools:
    def __init__(self):
        pass

    def get_spreadsheet_schema(self, filename: str) -> str:
        """
        Retrieves the schema of a CSV or Excel file (sheet names, column headers, and data types).
        Use this first to inspect the data structure before writing python pandas code.
        
        :param filename: The name of the CSV or Excel file to inspect.
        :return: A markdown summary of the spreadsheet schema.
        """
        filepath = self._resolve_path(filename)
        if not filepath:
            return f"Error: File '{filename}' not found."
            
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
                return "Error: Unsupported file format."
        except Exception as e:
            return f"Error reading schema: {str(e)}"

    def run_pandas_code(self, filename: str, code: str) -> str:
        """
        Executes a Python code block using pandas on the specified spreadsheet file.
        - If Excel has ONE sheet, it is pre-loaded into DataFrame 'df'.
        - If Excel has MULTIPLE sheets, they are loaded into a dict of DataFrames named 'sheets' (e.g. `df = sheets['Q2_Sales']`).
        - The result must be stored in the 'result' variable.
        
        :param filename: The name or path of the CSV or Excel file.
        :param code: The Python code to execute. Store your final result in the variable 'result' (e.g., `result = df.sum()`).
        :return: The string representation of the 'result' variable.
        """
        filepath = self._resolve_path(filename)
        if not filepath:
            return f"Error: File '{filename}' not found."
            
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
                sheets = {"default": df}
            elif filepath.endswith(('.xlsx', '.xls')):
                # Load all sheets as dict of DataFrames
                sheets = pd.read_excel(filepath, sheet_name=None)
                if len(sheets) == 1:
                    df = list(sheets.values())[0]
                else:
                    df = None
            else:
                return "Error: Unsupported file format."
        except Exception as e:
            return f"Error loading file: {str(e)}"
            
        # Prepare context for execution
        local_vars = {
            'sheets': sheets,
            'df': df,
            'pd': pd,
            'result': None
        }
        
        try:
            # Note: Execute safely. Standard Python sandbox recommendations apply.
            exec(code, {}, local_vars)
            result = local_vars.get('result')
            if result is None:
                return "Code executed successfully, but 'result' variable was not set. Please assign your final output to the 'result' variable."
            return str(result)
        except Exception as e:
            return f"Error executing code: {str(e)}"

    def _resolve_path(self, filename: str) -> str:
        search_paths = [
            "/media/hirthikbalaji/AGPT DATA/SAMPLE",
            "/app/backend/data/uploads",
            "/mnt/uploads",
            "./backend/data/uploads",
            ".",
        ]
        for path in search_paths:
            full_path = os.path.join(path, filename)
            if os.path.exists(full_path):
                return full_path
                
        # Glob matching fallback
        for path in search_paths:
            matches = glob.glob(os.path.join(path, f"*{filename}*"))
            if matches:
                return matches[0]
        return None

