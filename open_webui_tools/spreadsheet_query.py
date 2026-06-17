"""
title: Excel & CSV Spreadsheet Analyzer
author: Advanced Agentic RAG Team
version: 1.1.0
description: Executes Python/Pandas analytical queries on CSV or Excel files. Invoke ONLY when the user explicitly asks you to compute, aggregate, filter, or summarize spreadsheet data. Do NOT use for greetings or general questions.
requirements: pandas, openpyxl
"""

import os
import glob
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import pandas as pd

class Tools:
    class Valves(BaseModel):
        SHAREPOINT_LOCAL_PATH: str = Field(
            default="/media/hirthikbalaji/AGPT DATA/SAMPLE",
            description="Absolute path to your synced SharePoint or OneDrive folder containing local spreadsheets."
        )

    def __init__(self):
        self.valves = self.Valves()

    def get_spreadsheet_schema(self, filename: str) -> str:
        """
        Retrieves the sheet names and columns of a spreadsheet. Call this first to understand sheet/column structures before running queries.
        
        :param filename: The name of the Excel or CSV file (e.g. 'sales.xlsx').
        :return: A markdown summary of the spreadsheet schema.
        """
        filepath = self._resolve_path(filename)
        if not filepath:
            return f"Error: File '{filename}' not found in the SharePoint directory."
            
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
        Executes python pandas code to calculate totals, filter rows, or summarize columns on a spreadsheet.
        - Exposes 'df' if there is one sheet, or a dictionary 'sheets' of DataFrames if there are multiple sheets.
        - Your code must assign the final calculation or table result to the 'result' variable.
        
        :param filename: The name of the Excel or CSV file.
        :param code: The Python code to run. Assign the output to 'result' (e.g. `result = df['Sales'].sum()`).
        :return: The string representation of the 'result' variable.
        """
        filepath = self._resolve_path(filename)
        if not filepath:
            return f"Error: File '{filename}' not found in the SharePoint directory."
            
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
                sheets = {"default": df}
            elif filepath.endswith(('.xlsx', '.xls')):
                sheets = pd.read_excel(filepath, sheet_name=None)
                if len(sheets) == 1:
                    df = list(sheets.values())[0]
                else:
                    df = None
            else:
                return "Error: Unsupported file format."
        except Exception as e:
            return f"Error loading file: {str(e)}"
            
        local_vars = {
            'sheets': sheets,
            'df': df,
            'pd': pd,
            'result': None
        }
        
        try:
            exec(code, {}, local_vars)
            result = local_vars.get('result')
            if result is None:
                return "Code executed successfully, but 'result' variable was not set."
            return str(result)
        except Exception as e:
            return f"Error executing code: {str(e)}"

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
