#!/usr/bin/env python3
"""
MCP (Model Context Protocol) File Analyzer Server

This server provides file structure analysis capabilities to Cursor agent
by leveraging the existing FileAnalyzer functionality.
"""

import json
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Add the current directory to Python path to import core modules
sys.path.insert(0, str(Path(__file__).parent))

from core.analyzer import FileAnalyzer


class MCPFileAnalyzer:
    """
    MCP server for file structure analysis.
    
    Provides file analysis capabilities to Cursor agent through MCP protocol.
    Uses existing FileAnalyzer for actual file parsing and analysis.
    """
    
    def __init__(self):
        """Initialize MCP File Analyzer with FileAnalyzer instance."""
        self.analyzer = FileAnalyzer(".")  # Use current directory as base
    
    def get_file_structure(self, file_path: str) -> Dict[str, Any]:
        """
        MCP method for file structure analysis.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Dictionary containing structured file analysis data
        """
        try:
            # Validate and normalize file path
            normalized_path = self._validate_file_path(file_path)
            
            # Use existing FileAnalyzer to get JSON description
            json_result = self.analyzer.describe_file(
                normalized_path, 
                format='json', 
                include_docs=True
            )
            
            # Parse JSON string to dictionary for MCP response
            if json_result.startswith("Error:"):
                return {
                    "error": json_result,
                    "file": str(normalized_path),
                    "summary": {"lines": 0, "classes": 0, "functions": 0, "variables": 0},
                    "classes": [],
                    "functions": [],
                    "variables": []
                }
            
            return json.loads(json_result)
            
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}",
                "file": file_path,
                "summary": {"lines": 0, "classes": 0, "functions": 0, "variables": 0},
                "classes": [],
                "functions": [],
                "variables": []
            }
    
    def _validate_file_path(self, file_path: str) -> Path:
        """
        Validate and normalize file path.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Normalized Path object
            
        Raises:
            ValueError: If file path is invalid
        """
        if not file_path:
            raise ValueError("File path cannot be empty")
        
        # Convert to Path object
        path = Path(file_path)
        
        # Resolve relative paths
        if not path.is_absolute():
            path = Path.cwd() / path
        
        # Check if file exists
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Check if it's a Python file
        if path.suffix.lower() != '.py':
            raise ValueError(f"File must be a Python file (.py), got: {path.suffix}")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        return path
    
    def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP protocol requests.
        
        Args:
            request: MCP request dictionary
            
        Returns:
            MCP response dictionary
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "py-analyzer",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "notifications/initialized" or method == "initialized":
                # Notification, no response needed
                return None
                
            elif method == "ping":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {}
                }
                
            elif method == "tools/list":
                tools = [
                    {
                        "name": "get_file_structure",
                        "description": "Analyze Python file structure and return detailed class/function information. \n\nUSE THIS TOOL WHEN:\n- You need to understand the architecture of a Python file\n- You want to find all classes, methods, functions, and their relationships\n- You're analyzing code for documentation or refactoring\n- You need structured data about Python code structure\n- You're debugging import or dependency issues\n\nTHIS TOOL PROVIDES:\n- Complete class hierarchy with inheritance relationships\n- Method signatures with visibility (public/private/protected)\n- Function definitions and their documentation\n- Type annotations and field information\n- Structured JSON output for programmatic analysis\n\nREQUIREMENTS:\n- File must be a valid Python (.py) file\n- File must be accessible and readable\n\nEXAMPLE USAGE:\n- 'Analyze the structure of core/parser.py to understand the PythonParser class'\n- 'Get all classes and methods from a complex module to understand its API'\n- 'Extract class hierarchy for documentation generation'",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the Python file to analyze (relative or absolute)"
                                }
                            },
                            "required": ["file_path"]
                        }
                    }
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "get_file_structure":
                    file_path = arguments.get("file_path")
                    if not file_path:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32602,
                                "message": "Missing required parameter: file_path"
                            }
                        }
                    
                    result = self.get_file_structure(file_path)
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                    "data": traceback.format_exc()
                }
            }


def main():
    """Main entry point for MCP server."""
    analyzer = MCPFileAnalyzer()
    
    # MCP protocol implementation
    print("MCP File Analyzer Server started")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
                response = analyzer.handle_mcp_request(request)
                
                if response is not None:
                    print(json.dumps(response, ensure_ascii=False), flush=True)
                    
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Server error: {str(e)}"
            }
        }), flush=True)


if __name__ == "__main__":
    main() 