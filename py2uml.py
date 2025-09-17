#!/usr/bin/env python3
"""
py2uml - Standalone Python to PlantUML converter
A single-file script that generates UML diagrams from Python source code.

This is a completely standalone version that includes all functionality in one file.
No installation required - just download and run!

Usage:
    python py2uml.py generate <directory> [output_file] [--no-gitignore] [--use-gitignore]
    python py2uml.py describe <file> [--format text|json|yaml] [--no-docs]

Examples:
    python py2uml.py generate src/
    python py2uml.py generate src/ output.puml
    python py2uml.py generate src/ output.puml --no-gitignore
    python py2uml.py describe src/models.py
    python py2uml.py describe src/models.py --format json
    python py2uml.py describe src/models.py --format yaml --no-docs

Features:
    - Complete UML diagram generation from Python code
    - File analysis with multiple output formats (text, JSON, YAML)
    - .gitignore support for filtering files
    - Error handling and partial parsing
    - No external dependencies (except optional PyYAML and pathspec)
    - Self-contained - works without the full project structure

Author: py2puml project
License: MIT
"""

import ast
import json
import os
import sys
import warnings
import fnmatch
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Check for optional dependencies
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import pathspec
    PATHSPEC_AVAILABLE = True
except ImportError:
    PATHSPEC_AVAILABLE = False


class PythonParser:
    """Handles parsing of Python source code to extract classes, functions, and variables."""
    
    def __init__(self):
        """Initialize Python parser."""
        self.errors = []
        self.files_with_errors = {}
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a Python file to extract class and function definitions."""
        try:
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                self.errors.append(error_msg)
                self.files_with_errors[str(file_path)] = [error_msg]
                print(f"Warning: {error_msg}")
                return {"classes": [], "functions": [], "global_vars": [], "class_bases": {}}
            
            if not os.access(file_path, os.R_OK):
                error_msg = f"Permission denied reading file: {file_path}"
                self.errors.append(error_msg)
                self.files_with_errors[str(file_path)] = [error_msg]
                print(f"Warning: {error_msg}")
                return {"classes": [], "functions": [], "global_vars": [], "class_bases": {}}
            
            with open(file_path, "r", encoding='utf-8') as file:
                try:
                    content = file.read()
                    # Suppress syntax warnings for invalid escape sequences
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=SyntaxWarning)
                        node = ast.parse(content, filename=file_path.name)
                except SyntaxError as e:
                    error_msg = f"Syntax error in {file_path}: {e}"
                    self.errors.append(error_msg)
                    self.files_with_errors[str(file_path)] = [error_msg]
                    print(f"Warning: {error_msg}")
                    return self._parse_file_partially(content, file_path)
                except UnicodeDecodeError as e:
                    error_msg = f"Encoding error in {file_path}: {e}"
                    self.errors.append(error_msg)
                    self.files_with_errors[str(file_path)] = [error_msg]
                    print(f"Warning: {error_msg}")
                    return {"classes": [], "functions": [], "global_vars": [], "class_bases": {}}
                
        except Exception as e:
            error_msg = f"Unexpected error reading {file_path}: {e}"
            self.errors.append(error_msg)
            self.files_with_errors[str(file_path)] = [error_msg]
            print(f"Warning: {error_msg}")
            return {"classes": [], "functions": [], "global_vars": [], "class_bases": {}}
        
        classes = []
        functions = []
        class_bases = {}
        global_vars = []
        
        try:
            for n in node.body:
                if isinstance(n, ast.ClassDef):
                    try:
                        class_name, fields, attributes, static_methods, methods, properties, abstract_method_count = self._process_class_def(n)
                        total_method_count = len(static_methods) + len(methods)
                        bases = [base.id for base in n.bases if isinstance(base, ast.Name)]
                        decorators = self._extract_decorators(n)
                        class_type = self._determine_class_type(len(fields) > 0, abstract_method_count, total_method_count, bases, decorators)
                        class_bases[class_name] = bases
                        classes.append((
                            class_name,
                            sorted(list(set(fields)), key=lambda x: x[1]),
                            sorted(list(set(attributes)), key=lambda x: x[1]),
                            sorted(list(set(static_methods)), key=lambda x: x[1]),
                            sorted(list(set(methods)), key=lambda x: x[1]),
                            sorted(list(set(properties)), key=lambda x: x[1]),
                            class_type,
                            bases
                        ))
                    except Exception as e:
                        error_msg = f"Error processing class in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
                elif isinstance(n, ast.FunctionDef):
                    try:
                        if not self._is_decorator_function(n):
                            functions.append(self._process_function_def(n))
                    except Exception as e:
                        error_msg = f"Error processing function in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
                elif isinstance(n, ast.AsyncFunctionDef):
                    try:
                        if not self._is_decorator_function(n):
                            functions.append(self._process_function_def(n))
                    except Exception as e:
                        error_msg = f"Error processing async function in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
                elif isinstance(n, ast.Assign):
                    try:
                        global_vars.extend(self._process_global_vars(n))
                    except Exception as e:
                        error_msg = f"Error processing global variables in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
        except Exception as e:
            error_msg = f"Error processing AST nodes in {file_path}: {e}"
            self.errors.append(error_msg)
            if str(file_path) not in self.files_with_errors:
                self.files_with_errors[str(file_path)] = []
            self.files_with_errors[str(file_path)].append(error_msg)
            print(f"Warning: {error_msg}")
        
        return {
            "classes": classes,
            "functions": functions,
            "global_vars": global_vars,
            "class_bases": class_bases
        }
    
    def parse_directory(self, directory_path: Path) -> List[Dict[str, Any]]:
        """Parse all Python files in a directory."""
        results = []
        python_files = list(directory_path.rglob("*.py"))
        
        for file_path in python_files:
            result = self.parse_file(file_path)
            result["file_path"] = file_path
            results.append(result)
        
        return results
    
    def _parse_file_partially(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Attempt partial parsing of a file with syntax errors."""
        def try_parse_class_block(class_text: str, class_name: str) -> Tuple[str, List, List, List, List, List, int]:
            try:
                class_node = ast.parse(class_text)
                for node in class_node.body:
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        return self._process_class_def(node)
            except:
                pass
            return "UnknownClass", [], [], [], [], [], 0
        
        lines = content.split('\n')
        classes = []
        functions = []
        global_vars = []
        class_bases = {}
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('class '):
                class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                bases = []
                if '(' in line and ')' in line:
                    base_part = line.split('(')[1].split(')')[0]
                    bases = [base.strip() for base in base_part.split(',') if base.strip()]
                
                class_lines = [line]
                brace_count = line.count('{') - line.count('}')
                i += 1
                while i < len(lines) and brace_count > 0:
                    class_lines.append(lines[i])
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1
                
                class_text = '\n'.join(class_lines)
                class_name_parsed, fields, attributes, static_methods, methods, properties, abstract_method_count = try_parse_class_block(class_text, class_name)
                class_bases[class_name] = bases
                classes.append((
                    class_name,
                    sorted(list(set(fields)), key=lambda x: x[1]),
                    sorted(list(set(attributes)), key=lambda x: x[1]),
                    sorted(list(set(static_methods)), key=lambda x: x[1]),
                    sorted(list(set(methods)), key=lambda x: x[1]),
                    sorted(list(set(properties)), key=lambda x: x[1]),
                    "class",
                    bases
                ))
            elif line.startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                functions.append(f"+ {func_name}()")
            i += 1
        
        return {
            "classes": classes,
            "functions": functions,
            "global_vars": global_vars,
            "class_bases": class_bases
        }
    
    def _process_class_def(self, node: ast.ClassDef) -> Tuple[str, List, List, List, List, List, int]:
        """Process a class definition node to extract its components."""
        try:
            # Extract decorators and format class name
            decorators = self._extract_decorators(node)
            class_name = self._format_name_with_decorators(node.name, decorators)
            methods = []
            fields = []
            attributes = []
            properties = []
            abstract_method_count = 0
            static_methods = []
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    try:
                        # Check if this is a property
                        is_property = self._is_property_method(body_item)
                        is_property_setter_deleter = self._is_property_setter_or_deleter(body_item)
                        
                        if is_property:
                            property_info = self._process_property_method(body_item, node.body)
                            if property_info:
                                properties.append(property_info)
                        elif not is_property_setter_deleter:
                            # Skip property setters and deleters - they are handled by the main property
                            prefix, method_signature, is_abstract, is_static, is_class = self._process_method_def(body_item)
                            if is_abstract:
                                abstract_method_count += 1
                            if is_static or is_class:
                                static_methods.append((prefix, method_signature))
                            else:
                                methods.append((prefix, method_signature))

                        if body_item.name == '__init__':
                            fields = self._extract_fields_from_init(body_item)
                    except Exception as e:
                        continue

                elif isinstance(body_item, ast.AsyncFunctionDef):
                    try:
                        prefix, method_signature, is_abstract, is_static, is_class = self._process_method_def(body_item)
                        if is_abstract:
                            abstract_method_count += 1
                        if is_static or is_class:
                            static_methods.append((prefix, method_signature))
                        else:
                            methods.append((prefix, method_signature))
                    except Exception as e:
                        continue

                elif isinstance(body_item, ast.AnnAssign):
                    try:
                        attributes.extend(self._process_attributes(body_item))
                    except Exception as e:
                        continue
            return class_name, fields, attributes, static_methods, methods, properties, abstract_method_count
        except Exception as e:
            return "UnknownClass", [], [], [], [], [], 0
    
    def _process_method_def(self, body_item: ast.FunctionDef) -> Tuple[str, str, bool, bool, bool]:
        """Process a method definition node to extract its signature and properties."""
        try:
            # Extract decorators and format method name
            decorators = self._extract_decorators(body_item)
            
            # Determine method type first
            is_abstract = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'abstractmethod' for dec in body_item.decorator_list)
            is_static = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'staticmethod' for dec in body_item.decorator_list)
            is_class = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'classmethod' for dec in body_item.decorator_list)
            
            # For static, class, and abstract methods, exclude their decorators from name
            if is_static or is_class or is_abstract:
                # Remove staticmethod/classmethod/abstractmethod decorators from the list
                filtered_decorators = [d for d in decorators if d not in ['staticmethod', 'classmethod', 'abstractmethod']]
                method_name = self._format_name_with_decorators(body_item.name, filtered_decorators)
            else:
                method_name = self._format_name_with_decorators(body_item.name, decorators)
            
            prefix, vis_type = self._visibility(body_item.name)
            
            args = [arg.arg for arg in body_item.args.args]
            
            if is_class and args and args[0] == 'cls':
                args = args[1:]
            elif not is_static and not is_class and args and args[0] == 'self':
                args = args[1:]
            
            method_signature = f"{method_name}({', '.join(args)})"
            if is_abstract:
                prefix = prefix + ' {abstract}'
            elif is_static:
                prefix = prefix + ' {static}'
            return prefix, method_signature, is_abstract, is_static, is_class
        except Exception as e:
            return '+', f"{body_item.name if hasattr(body_item, 'name') else 'unknown'}()", False, False, False
    
    def _process_attributes(self, body_item: ast.AnnAssign) -> List[Tuple[str, str]]:
        """Process attributes of a class defined using type annotations."""
        try:
            if hasattr(body_item, 'target') and hasattr(body_item.target, 'id'):
                attr_name = body_item.target.id
                prefix, vis_type = self._visibility(attr_name)
                
                type_annotation = ""
                if body_item.annotation:
                    type_annotation = self._get_type_annotation(body_item.annotation)
                
                return [(prefix, f"{attr_name}: {type_annotation}")]
        except Exception as e:
            pass
        return []
    
    def _get_type_annotation(self, annotation: ast.AST) -> str:
        """Extract type annotation as string."""
        try:
            if isinstance(annotation, ast.Name):
                return annotation.id
            elif isinstance(annotation, ast.Constant):
                return str(annotation.value)
            elif isinstance(annotation, ast.Attribute):
                return f"{self._get_type_annotation(annotation.value)}.{annotation.attr}"
            elif isinstance(annotation, ast.Subscript):
                return f"{self._get_type_annotation(annotation.value)}[{self._get_type_annotation(annotation.slice)}]"
            else:
                return str(annotation)
        except Exception as e:
            return "Any"
    
    def _process_function_def(self, node: ast.FunctionDef) -> str:
        """Process a function definition node."""
        try:
            # Extract decorators and format function name
            decorators = self._extract_decorators(node)
            function_name = self._format_name_with_decorators(node.name, decorators)
            
            prefix, vis_type = self._visibility(node.name)
            args = []
            
            for arg in node.args.args:
                arg_name = arg.arg
                if arg.annotation:
                    arg_type = self._get_type_annotation(arg.annotation)
                    args.append(f"{arg_name}: {arg_type}")
                else:
                    args.append(arg_name)
            
            function_signature = f"{prefix} {function_name}({', '.join(args)})"
            return function_signature
        except Exception as e:
            return f"+ {node.name if hasattr(node, 'name') else 'unknown'}()"
    
    def _process_global_vars(self, node: ast.Assign) -> List[Tuple[str, str]]:
        """Process global variable assignments."""
        try:
            variables = []
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    prefix, vis_type = self._visibility(var_name)
                    variables.append((prefix, var_name))
            return variables
        except Exception as e:
            return []
    
    def _determine_class_type(self, has_fields: bool, abstract_method_count: int, total_method_count: int, bases: Optional[List[str]] = None, decorators: Optional[List[str]] = None) -> str:
        """Determine the type of class based on its characteristics and decorators."""
        # Check for dataclass decorator first
        if decorators and 'dataclass' in decorators:
            return "dataclass"
        
        if abstract_method_count > 0:
            return "abstract class"
        elif has_fields and total_method_count == 0:
            return "dataclass"
        elif total_method_count == 0:
            return "interface"
        else:
            return "class"
    
    def _extract_fields_from_init(self, init_method: ast.FunctionDef) -> List[Tuple[str, str]]:
        """Extract field assignments from __init__ method."""
        try:
            fields = []
            for item in init_method.body:
                if isinstance(item, ast.Assign):
                    fields.extend(self._process_fields(item))
            return fields
        except Exception as e:
            return []
    
    def _process_fields(self, body_item: ast.Assign) -> List[Tuple[str, str]]:
        """Process field assignments in class."""
        try:
            fields = []
            for target in body_item.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                    field_name = target.attr
                    prefix, vis_type = self._visibility(field_name)
                    fields.append((prefix, field_name))
            return fields
        except Exception as e:
            return []
    
    def _visibility(self, name: str) -> Tuple[str, str]:
        """Determine the visibility of a member based on its name."""
        if name.startswith('__') and name.endswith('__'):
            return '~', 'private'  # Magic
        if name.startswith('__'):
            return '-', 'private'  # Private
        elif name.startswith('_'):
            return '#', 'protected'  # Protected
        else:
            return '+', 'public'  # Public 
    
    def _extract_decorators(self, node: ast.AST) -> List[str]:
        """
        Extract decorator names from AST node (function or class).
        """
        decorators = []
        if hasattr(node, 'decorator_list') and node.decorator_list:
            for decorator in node.decorator_list:
                decorator_name = self._get_decorator_name(decorator)
                if decorator_name:
                    decorators.append(decorator_name)
        return decorators
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """
        Get decorator name from AST decorator node.
        """
        try:
            if isinstance(decorator, ast.Name):
                return decorator.id
            elif isinstance(decorator, ast.Attribute):
                # Handle cases like @property.setter
                if isinstance(decorator.value, ast.Name):
                    return f"{decorator.value.id}.{decorator.attr}"
                else:
                    return decorator.attr
            elif isinstance(decorator, ast.Call):
                # Handle cases like @dataclass(frozen=True)
                if isinstance(decorator.func, ast.Name):
                    return decorator.func.id
                elif isinstance(decorator.func, ast.Attribute):
                    return decorator.func.attr
            return "unknown"
        except Exception:
            return "unknown"
    
    def _format_name_with_decorators(self, name: str, decorators: List[str]) -> str:
        """
        Format name with decorator suffixes.
        """
        if not decorators:
            return name
        
        # Sort decorators for consistent output
        sorted_decorators = sorted(decorators)
        decorator_suffix = "".join(f"@{d}" for d in sorted_decorators)
        return f"{name}{decorator_suffix}"
    
    def _is_decorator_function(self, node: ast.FunctionDef) -> bool:
        """Check if a function is a decorator by analyzing its structure."""
        try:
            if hasattr(node, 'decorator_list') and node.decorator_list:
                return True
            
            if not node.body:
                return False
            
            for item in node.body:
                if isinstance(item, ast.Return):
                    if isinstance(item.value, ast.Name):
                        param_names = [arg.arg for arg in node.args.args]
                        if item.value.id in param_names:
                            if len(node.args.args) == 1 and item.value.id == node.args.args[0].arg:
                                return False
                            return False
                    elif isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Name):
                        if isinstance(item.value.func, ast.Name):
                            param_names = [arg.arg for arg in node.args.args]
                            if item.value.func.id in param_names:
                                return True
                        return False
                elif isinstance(item, ast.FunctionDef):
                    return True
            
            return False
        except Exception:
            return False
    
    def _is_property_method(self, node: ast.FunctionDef) -> bool:
        """Check if a method is a property (has @property decorator)."""
        try:
            if hasattr(node, 'decorator_list') and node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'property':
                        return True
            return False
        except Exception:
            return False
    
    def _is_property_setter_or_deleter(self, node: ast.FunctionDef) -> bool:
        """Check if a method is a property setter or deleter (has @property.setter or @property.deleter decorator)."""
        try:
            if hasattr(node, 'decorator_list') and node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if (isinstance(decorator.value, ast.Name) and 
                            decorator.value.id == node.name and 
                            decorator.attr in ['setter', 'deleter']):
                            return True
            return False
        except Exception:
            return False
    
    def _process_property_method(self, property_node: ast.FunctionDef, class_body: List[ast.AST]) -> Optional[Tuple[str, str]]:
        """Process a property method to determine its access level and return property info."""
        try:
            property_name = property_node.name
            prefix, _ = self._visibility(property_name)
            
            # Check for setter and deleter methods
            has_setter = False
            has_deleter = False
            
            for body_item in class_body:
                if isinstance(body_item, ast.FunctionDef) and body_item.name == property_name:
                    if hasattr(body_item, 'decorator_list') and body_item.decorator_list:
                        for decorator in body_item.decorator_list:
                            if isinstance(decorator, ast.Attribute):
                                if (isinstance(decorator.value, ast.Name) and 
                                    decorator.value.id == property_name and 
                                    decorator.attr == 'setter'):
                                    has_setter = True
                                elif (isinstance(decorator.value, ast.Name) and 
                                      decorator.value.id == property_name and 
                                      decorator.attr == 'deleter'):
                                    has_deleter = True
            
            # Determine access level
            if has_setter:
                # Check if getter raises AttributeError (write-only property)
                if self._getter_raises_attribute_error(property_node):
                    access_level = "{write only}"
                else:
                    access_level = "{read write}"
            else:
                access_level = "{read only}"
            
            # Get return type annotation if available
            return_type = ""
            if property_node.returns:
                return_type = f": {self._get_type_annotation(property_node.returns)}"
            
            property_signature = f"{property_name}{return_type} {access_level}"
            return (prefix, property_signature)
            
        except Exception:
            return None
    
    def _getter_raises_attribute_error(self, property_node: ast.FunctionDef) -> bool:
        """Check if the property getter raises AttributeError (indicating write-only property)."""
        try:
            for item in property_node.body:
                if isinstance(item, ast.Raise):
                    if isinstance(item.exc, ast.Name) and item.exc.id == 'AttributeError':
                        return True
                    elif isinstance(item.exc, ast.Call) and isinstance(item.exc.func, ast.Name):
                        if item.exc.func.id == 'AttributeError':
                            return True
            return False
        except Exception:
            return False


class FileFilter:
    """Handles file filtering based on .gitignore patterns."""
    
    def __init__(self, directory_path: str, use_gitignore: bool = True):
        """Initialize file filter."""
        self.directory = Path(directory_path)
        self.use_gitignore = use_gitignore
        self.gitignore_specs = {}
        
        if self.use_gitignore:
            self._load_gitignore_patterns()
    
    def should_ignore(self, file_path: Path) -> bool:
        """Check if a file should be ignored based on .gitignore patterns."""
        if file_path.name.startswith('.'):
            return True
        
        if not self.use_gitignore:
            return False
        
        if PATHSPEC_AVAILABLE:
            return self._should_ignore_pathspec(file_path)
        else:
            return self._should_ignore_simple(file_path)
    
    def _load_gitignore_patterns(self):
        """Load all .gitignore files in the project recursively."""
        try:
            gitignore_files = list(self.directory.rglob('.gitignore'))
            
            for gitignore_file in gitignore_files:
                try:
                    gitignore_dir = gitignore_file.parent
                    if PATHSPEC_AVAILABLE:
                        with open(gitignore_file, 'r', encoding='utf-8') as f:
                            patterns = f.read().splitlines()
                        spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
                        self.gitignore_specs[str(gitignore_dir)] = spec
                    else:
                        patterns = self._load_simple_gitignore_patterns(gitignore_file)
                        self.gitignore_specs[str(gitignore_dir)] = patterns
                except Exception as e:
                    print(f"Warning: Error reading .gitignore file {gitignore_file}: {e}", file=sys.stderr)
                    continue
        except Exception as e:
            print(f"Warning: Error loading .gitignore patterns: {e}", file=sys.stderr)
    
    def _load_simple_gitignore_patterns(self, gitignore_file):
        """Simple implementation for .gitignore patterns without pathspec."""
        try:
            patterns = []
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            return patterns
        except Exception as e:
            print(f"Warning: Error reading .gitignore file {gitignore_file}: {e}", file=sys.stderr)
            return []
    
    def _should_ignore_pathspec(self, file_path: Path) -> bool:
        """Check if file should be ignored using pathspec library."""
        try:
            relative_path = file_path.relative_to(self.directory)
            
            for gitignore_dir, spec in self.gitignore_specs.items():
                gitignore_path = Path(gitignore_dir)
                if gitignore_path in file_path.parents or gitignore_path == file_path.parent:
                    try:
                        relative_to_gitignore = file_path.relative_to(gitignore_path)
                        if spec.match_file(relative_to_gitignore):
                            return True
                    except ValueError:
                        continue
            return False
        except Exception as e:
            print(f"Warning: Error checking .gitignore for {file_path}: {e}", file=sys.stderr)
            return False
    
    def _should_ignore_simple(self, file_path: Path) -> bool:
        """Simple implementation for checking .gitignore patterns."""
        try:
            relative_path = file_path.relative_to(self.directory)
            
            for gitignore_dir, spec in self.gitignore_specs.items():
                gitignore_path = Path(gitignore_dir)
                if gitignore_path in file_path.parents or gitignore_path == file_path.parent:
                    try:
                        relative_to_gitignore = file_path.relative_to(gitignore_path)
                        relative_str = str(relative_to_gitignore).replace('\\', '/')
                        
                        if hasattr(spec, 'match_file'):
                            continue
                        
                        for pattern in spec:
                            if self._match_simple_pattern(relative_str, pattern):
                                return True
                    except ValueError:
                        continue
            return False
        except Exception as e:
            print(f"Warning: Error checking .gitignore for {file_path}: {e}", file=sys.stderr)
            return False
    
    def _match_simple_pattern(self, file_path: str, pattern: str) -> bool:
        """Simple pattern matching for .gitignore patterns."""
        if pattern.startswith('/'):
            pattern = pattern[1:]
        
        if '**' in pattern:
            pattern = pattern.replace('**', '*')
        
        if pattern.startswith('!'):
            return False
        
        if pattern.endswith('/'):
            return file_path.startswith(pattern)
        
        return fnmatch.fnmatch(file_path, pattern)


class UMLGenerator:
    """Handles generation of UML diagrams from Python source code."""
    
    def __init__(self, directory_path: str, file_filter: FileFilter):
        """Initialize UML generator."""
        self.directory = Path(directory_path)
        self.file_filter = file_filter
        self.parser = PythonParser()
        self.uml = '@startuml\n'
        self.all_class_bases = {}
        self.errors = []
        self.files_with_errors = {}
    
    def generate_uml(self) -> str:
        """Generate UML for all Python files in the specified directory."""
        try:
            if not self.directory.exists():
                error_msg = f"Directory not found: {self.directory}"
                self.errors.append(error_msg)
                print(f"Error: {error_msg}")
                return "@startuml\n@enduml"
            
            if not os.access(self.directory, os.R_OK):
                error_msg = f"Permission denied reading directory: {self.directory}"
                self.errors.append(error_msg)
                print(f"Error: {error_msg}")
                return "@startuml\n@enduml"
            
            pathlist = list(self.directory.rglob('*.py'))
            
            if self.file_filter.use_gitignore:
                original_count = len(pathlist)
                pathlist = [path for path in pathlist if not self.file_filter.should_ignore(path)]
                ignored_count = original_count - len(pathlist)
                if ignored_count > 0:
                    print(f"Info: {ignored_count} Python files ignored due to .gitignore patterns")
            
            if not pathlist:
                print(f"Warning: No Python files found in {self.directory}")
                return "@startuml\nnote right of \"Empty Directory\"\nDirectory is empty\nend note\n@enduml"
                
        except Exception as e:
            error_msg = f"Error scanning directory {self.directory}: {e}"
            self.errors.append(error_msg)
            print(f"Error: {error_msg}")
            return "@startuml\n@enduml"
        
        for path in pathlist:
            try:
                relative_path = path.relative_to(self.directory).with_suffix('')
                package_name = str(relative_path).replace('/', '.').replace('\\', '.')
                
                parsed_data = self.parser.parse_file(path)
                class_infos = parsed_data["classes"]
                function_infos = parsed_data["functions"]
                global_vars = parsed_data["global_vars"]
                class_bases = parsed_data["class_bases"]

                self.errors.extend(self.parser.errors)
                self.files_with_errors.update(self.parser.files_with_errors)

                self.all_class_bases.update(class_bases)
                
                file_has_errors = str(path) in self.parser.files_with_errors
                
                if file_has_errors:
                    self.uml += f'package "{package_name}" <<Frame>> #FF0000 {{\n'
                else:
                    self.uml += f'package "{package_name}" <<Frame>> #F0F0FF {{\n'
                
                if global_vars:
                    self.uml += '  class "Global Variables" << (V,#AAAAFF) >> {\n'
                    for prefix, var in global_vars:
                        self.uml += f"    {prefix} {var}\n"
                    self.uml += '  }\n'
                for function_signature in function_infos:
                    self.uml += f'  class "{function_signature}" << (F,#DDDD00) >> {{\n  }}\n'
                for class_info in class_infos:
                    self.uml += self._format_class_info(class_info)

                self.uml += '}\n'
                
                # Add error notes after package closure
                if file_has_errors:
                    self.uml += f'\nnote right of "{package_name}"\n'
                    self.uml += 'Errors:\n'
                    for error in self.parser.files_with_errors[str(path)]:
                        self.uml += f'- {error}\n'
                    self.uml += 'end note\n'
                
            except Exception as e:
                error_msg = f"Error processing file {path}: {e}"
                self.errors.append(error_msg)
                if str(path) not in self.files_with_errors:
                    self.files_with_errors[str(path)] = []
                self.files_with_errors[str(path)].append(error_msg)
                print(f"Warning: {error_msg}")
                continue
        
        try:
            self._add_inheritance_relations()
        except Exception as e:
            error_msg = f"Error adding inheritance relations: {e}"
            self.errors.append(error_msg)
            print(f"Warning: {error_msg}")
        
        self.uml += '@enduml'
        return self.uml
    
    def _format_class_info(self, class_info: tuple) -> str:
        """Format the information of a class for UML representation."""
        try:
            class_name, fields, attributes, static_methods, methods, properties, class_type, bases = class_info
            class_str = f"  {class_type} {class_name} {{\n"
            
            for prefix, field in fields:
                try:
                    class_str += f"    {prefix} {field}\n"
                except Exception as e:
                    continue
                    
            if len(fields) and (len(methods) or len(properties)):
                class_str += "    ....\n"

            # Process properties
            for prefix, property_info in properties:
                try:
                    class_str += f"    {prefix} {property_info}\n"
                except Exception as e:
                    continue

            for prefix, method in methods:
                try:
                    class_str += f"    {prefix} {method}\n"
                except Exception as e:
                    continue

            if (len(fields) or len(methods) or len(properties)) and (len(attributes) or len(static_methods)):
                class_str += "    __Static__\n"

            for prefix, attribute in attributes:
                try:
                    class_str += f"    {prefix} {attribute}\n"
                except Exception as e:
                    continue

            if len(attributes) and len(static_methods):
                class_str += "    ....\n"

            for prefix, method in static_methods:
                try:
                    class_str += f"    {prefix} {method}\n"
                except Exception as e:
                    continue

            class_str += "  }\n"
            return class_str
        except Exception as e:
            class_name = class_info[0] if len(class_info) > 0 else 'UnknownClass'
            return f"  class {class_name} {{\n  }}\n"
    
    def _add_inheritance_relations(self):
        """Add inheritance relationships between classes to the UML."""
        for class_name, bases in self.all_class_bases.items():
            for base in bases:
                self.uml += f"{base} <|-- {class_name}\n"


class FileAnalyzer:
    """Handles analysis of Python files for detailed description."""
    
    def __init__(self, directory_path: str):
        """Initialize file analyzer."""
        self.directory = Path(directory_path)
        self.parser = PythonParser()
    
    def describe_file(self, file_path: Path, format: str = 'text', include_docs: bool = True) -> str:
        """Describe a Python file with classes, functions, and variables."""
        if format not in ['text', 'json', 'yaml']:
            raise ValueError(f"Unsupported format: {format}")
        
        if format == 'yaml' and not YAML_AVAILABLE:
            raise ValueError("YAML format requires PyYAML library. Install with: pip install PyYAML")
        
        try:
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            if not file_path.exists():
                return f"Error: File not found: {file_path}"
            
            parsed_data = self.parser.parse_file(file_path)
            classes = parsed_data["classes"]
            functions = parsed_data["functions"]
            global_vars = parsed_data["global_vars"]
            
            summary = self._get_file_summary(file_path, classes, functions, global_vars)
            
            data = {
                'file': str(file_path),
                'summary': summary,
                'classes': [],
                'functions': [],
                'variables': []
            }
            
            for class_info in classes:
                class_name, fields, attributes, static_methods, methods, properties, class_type, bases = class_info
                
                class_doc = None
                if include_docs:
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
                    'properties': [],
                    'methods': []
                }
                
                for prefix, field in fields:
                    field_data = {
                        'name': field.split(':')[0].strip() if ':' in field else field,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'type': field.split(':')[1].strip() if ':' in field else None
                    }
                    class_data['fields'].append(field_data)
                
                # Process properties
                for prefix, property_info in properties:
                    property_name = property_info.split(':')[0].strip() if ':' in property_info else property_info.split(' ')[0]
                    property_data = {
                        'name': property_name,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'signature': property_info,
                        'access_level': self._extract_access_level(property_info)
                    }
                    class_data['properties'].append(property_data)
                
                for prefix, method in methods + static_methods:
                    method_name = method.split('(')[0]
                    method_data = {
                        'name': method_name,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'signature': method,
                        'return_type': None,
                        'documentation': None
                    }
                    
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
            
            for func_signature in functions:
                func_name = func_signature.split('(')[0]
                func_data = {
                    'name': func_name,
                    'visibility': 'public',
                    'signature': func_signature,
                    'return_type': None,
                    'documentation': None
                }
                
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
            
            for prefix, var in global_vars:
                var_data = {
                    'name': var,
                    'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                    'type': None,
                    'documentation': None
                }
                data['variables'].append(var_data)
            
            return self._format_output(data, format)
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_file_summary(self, file_path: Path, classes: List, functions: List, variables: List) -> Dict[str, int]:
        """Get file summary statistics."""
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
        """Extract documentation from AST node."""
        try:
            if hasattr(node, 'body') and node.body:
                first_item = node.body[0]
                if isinstance(first_item, ast.Expr) and isinstance(first_item.value, ast.Constant):
                    return first_item.value.value.strip()
                elif isinstance(first_item, ast.Expr) and isinstance(first_item.value, ast.Str):
                    return first_item.value.s.strip()
            return ""
        except Exception as e:
            return ""
    
    def _format_output(self, data: Dict[str, Any], format: str) -> str:
        """Format output data according to specified format."""
        if format == 'text':
            return self._format_describe_text(data)
        elif format == 'json':
            return self._format_describe_json(data)
        elif format == 'yaml':
            return self._format_describe_yaml(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_describe_text(self, data: Dict[str, Any]) -> str:
        """Format data as text output."""
        output = []
        
        output.append(f"File: {data['file']}")
        summary = data['summary']
        output.append(f"Summary: {summary['lines']} lines, {summary['classes']} classes, {summary['functions']} functions, {summary['variables']} variables")
        output.append("")
        
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
                
                if class_data['properties']:
                    output.append("    Properties:")
                    for property_item in class_data['properties']:
                        output.append(f"      {property_item['visibility']} {property_item['signature']}")
                        output.append(f"        Access: {property_item['access_level']}")
                
                if class_data['fields']:
                    output.append("    Fields:")
                    for field in class_data['fields']:
                        output.append(f"      {field['visibility']} {field['name']}")
                        if field['type']:
                            output.append(f"        Type: {field['type']}")
                output.append("")
        
        if data['functions']:
            output.append("Functions:")
            for func in data['functions']:
                output.append(f"  {func['visibility']} {func['signature']}")
                if func['documentation']:
                    output.append(f"    Documentation: {func['documentation']}")
            output.append("")
        
        if data['variables']:
            output.append("Variables:")
            for var in data['variables']:
                output.append(f"  {var['visibility']} {var['name']}")
                if var['type']:
                    output.append(f"    Type: {var['type']}")
            output.append("")
        
        return "\n".join(output)
    
    def _format_describe_json(self, data: Dict[str, Any]) -> str:
        """Format data as JSON output."""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _format_describe_yaml(self, data: Dict[str, Any]) -> str:
        """Format data as YAML output."""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    def _extract_access_level(self, property_info: str) -> str:
        """Extract access level from property info string."""
        if '{read write}' in property_info:
            return 'read write'
        elif '{read only}' in property_info:
            return 'read only'
        elif '{write only}' in property_info:
            return 'write only'
        else:
            return 'unknown'


def main():
    """Main CLI function."""
    if len(sys.argv) < 2:
        print("Usage: python py2uml.py <command> [options]")
        print("Commands:")
        print("  generate <directory> [output_file] [--no-gitignore] [--use-gitignore]")
        print("  describe <file> [--format text|json|yaml] [--no-docs]")
        print("")
        print("Examples:")
        print("  python py2uml.py generate src/")
        print("  python py2uml.py generate src/ output.puml")
        print("  python py2uml.py generate src/ output.puml --no-gitignore")
        print("  python py2uml.py describe src/models.py")
        print("  python py2uml.py describe src/models.py --format json")
        print("  python py2uml.py describe src/models.py --format yaml --no-docs")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        if len(sys.argv) < 3:
            print("Error: generate command requires directory argument")
            print("Usage: python py2uml.py generate <directory> [output_file] [--no-gitignore] [--use-gitignore]")
            sys.exit(1)
        
        directory = sys.argv[2]
        
        # Check if output_file is provided (not a flag)
        output_file = None
        if len(sys.argv) >= 4 and not sys.argv[3].startswith('--'):
            output_file = sys.argv[3]
        
        # If no output file specified, use index.puml in the analyzed directory
        if output_file is None:
            directory_path = Path(directory)
            output_file = str(directory_path / "index.puml")
        
        # Parse options
        no_gitignore = '--no-gitignore' in sys.argv
        use_gitignore = '--use-gitignore' in sys.argv
        
        # Determine gitignore usage
        use_gitignore_flag = True
        if no_gitignore:
            use_gitignore_flag = False
        elif use_gitignore:
            use_gitignore_flag = True
        
        try:
            # Validate directory
            directory_path = Path(directory)
            if not directory_path.exists():
                print(f"Error: Directory not found: {directory}")
                sys.exit(1)
            
            if not directory_path.is_dir():
                print(f"Error: Path is not a directory: {directory}")
                sys.exit(1)
            
            # Create output directory if needed
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file filter
            file_filter = FileFilter(str(directory_path), use_gitignore=use_gitignore_flag)
            
            # Create UML generator
            generator = UMLGenerator(str(directory_path), file_filter)
            
            # Generate UML
            uml_output = generator.generate_uml()
            
            # Write output to file
            try:
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(uml_output)
            except PermissionError:
                print(f"Error: Permission denied writing to {output_path}")
                sys.exit(1)
            except Exception as e:
                print(f"Error: Failed to write output file {output_path}: {e}")
                sys.exit(1)
            
            print(f"PlantUML code has been saved to {output_path}")
            
            # Print warnings if any
            all_warnings = generator.errors + generator.parser.errors
            if all_warnings:
                print(f"\nWarning: {len(all_warnings)} warnings occurred during processing:")
                for warning in all_warnings:
                    print(f"  - {warning}")
        
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "describe":
        if len(sys.argv) < 3:
            print("Error: describe command requires file argument")
            print("Usage: python py2uml.py describe <file> [--format text|json|yaml] [--no-docs]")
            sys.exit(1)
        
        file_path = sys.argv[2]
        
        # Parse options
        format_ = 'text'
        no_docs = False
        
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == '--format' and i + 1 < len(sys.argv):
                format_ = sys.argv[i + 1]
            elif arg == '--no-docs':
                no_docs = True
        
        try:
            # Validate file
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                print(f"Error: File not found: {file_path}")
                sys.exit(1)
            
            if not file_path_obj.is_file():
                print(f"Error: Path is not a file: {file_path}")
                sys.exit(1)
            
            # Validate format
            if format_ not in ['text', 'json', 'yaml']:
                print(f"Error: Unsupported format: {format_}. Supported formats: text, json, yaml")
                sys.exit(1)
            
            if format_ == 'yaml' and not YAML_AVAILABLE:
                print("Error: YAML format requires PyYAML library. Install with: pip install PyYAML")
                sys.exit(1)
            
            # Create analyzer
            analyzer = FileAnalyzer(str(file_path_obj.parent))
            
            # Describe file
            include_docs = not no_docs
            result = analyzer.describe_file(file_path_obj, format=format_, include_docs=include_docs)
            
            # Print result
            print(result)
            
            # Print warnings if any
            if analyzer.parser.errors:
                print(f"\nWarning: {len(analyzer.parser.errors)} warnings occurred during processing:")
                for warning in analyzer.parser.errors:
                    print(f"  - {warning}")
        
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    else:
        print(f"Error: Unknown command: {command}")
        print("Available commands: generate, describe")
        sys.exit(1)


if __name__ == "__main__":
    main()
