import ast
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

from .parser import PythonParser


class FileAnalyzer:
    """
    Handles analysis of Python files for detailed description.
    """
    
    def __init__(self, directory_path: str):
        """
        Initialize file analyzer.
        
        Args:
            directory_path: Path to the directory containing files to analyze
        """
        self.directory = Path(directory_path)
        self.parser = PythonParser()
    
    def describe_file(self, file_path: Path, format: str = 'text', include_docs: bool = True) -> str:
        """
        Describe a Python file with classes, functions, and variables.
        
        Args:
            file_path: Path to the Python file to describe
            format: Output format ('text', 'json', 'yaml')
            include_docs: Whether to include documentation
            
        Returns:
            Formatted description of the file
        """
        # Check format at the beginning
        if format not in ['text', 'json', 'yaml']:
            raise ValueError(f"Unsupported format: {format}")
        
        try:
            # Convert to Path object if string is passed
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # Check file existence
            if not file_path.exists():
                return f"Error: File not found: {file_path}"
            
            # Parse file
            parsed_data = self.parser.parse_file(file_path)
            classes = parsed_data["classes"]
            functions = parsed_data["functions"]
            global_vars = parsed_data["global_vars"]
            
            # Get file statistics
            summary = self._get_file_summary(file_path, classes, functions, global_vars)
            
            # Prepare data for formatting
            data = {
                'file': str(file_path),
                'summary': summary,
                'classes': [],
                'functions': [],
                'variables': []
            }
            
            # Process classes
            for class_info in classes:
                class_name, fields, attributes, static_methods, methods, class_type, bases = class_info
                
                # Extract class documentation
                class_doc = None
                if include_docs:
                    # Find AST node of the class to extract documentation
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef) and node.name == class_name:
                                class_doc = self._extract_documentation(node)
                                break
                    except Exception:
                        pass
                
                class_data = {
                    'name': class_name,
                    'type': class_type,
                    'bases': bases,
                    'documentation': class_doc,
                    'fields': [],
                    'methods': []
                }
                
                # Process fields
                for prefix, field in fields:
                    field_data = {
                        'name': field.split(':')[0].strip() if ':' in field else field,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'type': field.split(':')[1].strip() if ':' in field else None
                    }
                    class_data['fields'].append(field_data)
                
                # Process methods
                for prefix, method in methods + static_methods:
                    method_name = method.split('(')[0]
                    method_data = {
                        'name': method_name,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'signature': method,
                        'return_type': None,  # TODO: extract from annotations
                        'documentation': None
                    }
                    
                    # Extract method documentation
                    if include_docs:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                content = file.read()
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef) and node.name == class_name:
                                    for body_item in node.body:
                                        if isinstance(body_item, ast.FunctionDef) and body_item.name == method_name:
                                            method_data['documentation'] = self._extract_documentation(body_item)
                                            break
                                        elif isinstance(body_item, ast.AsyncFunctionDef) and body_item.name == method_name:
                                            method_data['documentation'] = self._extract_documentation(body_item)
                                            break
                                    break
                        except Exception:
                            pass
                    
                    class_data['methods'].append(method_data)
                
                data['classes'].append(class_data)
            
            # Process functions
            for func_signature in functions:
                func_name = func_signature.split('(')[0]
                func_data = {
                    'name': func_name,
                    'visibility': 'public',  # Functions are always public
                    'signature': func_signature,
                    'return_type': None,  # TODO: extract from annotations
                    'documentation': None
                }
                
                # Extract function documentation
                if include_docs:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                                func_data['documentation'] = self._extract_documentation(node)
                                break
                            elif isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
                                func_data['documentation'] = self._extract_documentation(node)
                                break
                    except Exception:
                        pass
                
                data['functions'].append(func_data)
            
            # Process variables
            for prefix, var in global_vars:
                var_data = {
                    'name': var,
                    'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                    'type': None,  # TODO: extract from annotations
                    'documentation': None
                }
                data['variables'].append(var_data)
            
            return self._format_output(data, format)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_file_summary(self, file_path: Path, classes: List, functions: List, variables: List) -> Dict[str, int]:
        """
        Get file summary statistics.
        
        Args:
            file_path: Path to the file
            classes: List of classes
            functions: List of functions
            variables: List of variables
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = len(file.readlines())
        except Exception:
            lines = 0
        
        return {
            'lines': lines,
            'classes': len(classes),
            'functions': len(functions),
            'variables': len(variables)
        }
    
    def _extract_documentation(self, node: ast.AST) -> str:
        """
        Extract documentation from AST node.
        
        Args:
            node: AST node to extract documentation from
            
        Returns:
            Documentation string or empty string if not found
        """
        try:
            if hasattr(node, 'body') and node.body:
                first_item = node.body[0]
                if isinstance(first_item, ast.Expr) and isinstance(first_item.value, ast.Constant):
                    return first_item.value.value.strip()
                elif isinstance(first_item, ast.Expr) and isinstance(first_item.value, ast.Str):
                    # For Python < 3.8
                    return first_item.value.s.strip()
            return ""
        except Exception as e:
            return ""
    
    def _format_output(self, data: Dict[str, Any], format: str) -> str:
        """
        Format output data according to specified format.
        
        Args:
            data: Data to format
            format: Output format ('text', 'json', 'yaml')
            
        Returns:
            Formatted string
        """
        if format == 'text':
            return self._format_describe_text(data)
        elif format == 'json':
            return self._format_describe_json(data)
        elif format == 'yaml':
            return self._format_describe_yaml(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_describe_text(self, data: Dict[str, Any]) -> str:
        """
        Format data as text output.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted text string
        """
        output = []
        
        # Header
        output.append(f"File: {data['file']}")
        summary = data['summary']
        output.append(f"Summary: {summary['lines']} lines, {summary['classes']} classes, {summary['functions']} functions, {summary['variables']} variables")
        output.append("")
        
        # Classes
        if data['classes']:
            output.append("Classes:")
            for class_data in data['classes']:
                output.append(f"  {class_data['name']} ({class_data['type']})")
                if class_data['bases']:
                    output.append(f"    Bases: {', '.join(class_data['bases'])}")
                if class_data['documentation']:
                    output.append(f"    Documentation: {class_data['documentation']}")
                
                if class_data['methods']:
                    output.append("    Methods:")
                    for method in class_data['methods']:
                        output.append(f"      {method['visibility']} {method['signature']}")
                        if method['documentation']:
                            output.append(f"        Documentation: {method['documentation']}")
                
                if class_data['fields']:
                    output.append("    Fields:")
                    for field in class_data['fields']:
                        output.append(f"      {field['visibility']} {field['name']}")
                        if field['type']:
                            output.append(f"        Type: {field['type']}")
                output.append("")
        
        # Functions
        if data['functions']:
            output.append("Functions:")
            for func in data['functions']:
                output.append(f"  {func['visibility']} {func['signature']}")
                if func['documentation']:
                    output.append(f"    Documentation: {func['documentation']}")
            output.append("")
        
        # Variables
        if data['variables']:
            output.append("Variables:")
            for var in data['variables']:
                output.append(f"  {var['visibility']} {var['name']}")
                if var['type']:
                    output.append(f"    Type: {var['type']}")
            output.append("")
        
        return "\n".join(output)
    
    def _format_describe_json(self, data: Dict[str, Any]) -> str:
        """
        Format data as JSON output.
        
        Args:
            data: Data to format
            
        Returns:
            JSON string
        """
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _format_describe_yaml(self, data: Dict[str, Any]) -> str:
        """
        Format data as YAML output.
        
        Args:
            data: Data to format
            
        Returns:
            YAML string
        """
        return yaml.dump(data, default_flow_style=False, allow_unicode=True) 