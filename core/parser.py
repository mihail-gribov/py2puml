import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


class PythonParser:
    """
    Handles parsing of Python source code to extract classes, functions, and variables.
    """
    
    def __init__(self):
        """Initialize Python parser."""
        self.errors = []  # List for storing errors
        self.files_with_errors = {}  # Dictionary for storing files with errors
    
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a Python file to extract class and function definitions, global variables, and class inheritance.
        
        Args:
            file_path: Path to the Python file to parse
            
        Returns:
            Dictionary containing parsed data with keys: classes, functions, global_vars, class_bases
        """
        try:
            # Check file existence
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                self.errors.append(error_msg)
                self.files_with_errors[str(file_path)] = [error_msg]
                print(f"Warning: {error_msg}")
                return {"classes": [], "functions": [], "global_vars": [], "class_bases": {}}
            
            # Check read permissions
            if not os.access(file_path, os.R_OK):
                error_msg = f"Permission denied reading file: {file_path}"
                self.errors.append(error_msg)
                self.files_with_errors[str(file_path)] = [error_msg]
                print(f"Warning: {error_msg}")
                return {"classes": [], "functions": [], "global_vars": [], "class_bases": {}}
            
            with open(file_path, "r", encoding='utf-8') as file:
                try:
                    content = file.read()
                    node = ast.parse(content, filename=file_path.name)
                except SyntaxError as e:
                    error_msg = f"Syntax error in {file_path}: {e}"
                    self.errors.append(error_msg)
                    self.files_with_errors[str(file_path)] = [error_msg]
                    print(f"Warning: {error_msg}")
                    # Attempt partial parsing of individual blocks
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
                        class_name, fields, attributes, static_methods, methods, abstract_method_count = self._process_class_def(n)
                        total_method_count = len(static_methods) + len(methods)
                        bases = [base.id for base in n.bases if isinstance(base, ast.Name)]
                        class_type = self._determine_class_type(len(fields) > 0, abstract_method_count, total_method_count, bases)
                        class_bases[class_name] = bases
                        classes.append((
                            class_name,
                            sorted(list(set(fields)), key=lambda x: x[1]),
                            sorted(list(set(attributes)), key=lambda x: x[1]),
                            sorted(list(set(static_methods)), key=lambda x: x[1]),
                            sorted(list(set(methods)), key=lambda x: x[1]),
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
                        # Check if function is a decorator
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
                        # Check if function is a decorator
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
        """
        Parse all Python files in a directory.
        
        Args:
            directory_path: Path to the directory to parse
            
        Returns:
            List of parsed data dictionaries for each file
        """
        results = []
        python_files = list(directory_path.rglob("*.py"))
        
        for file_path in python_files:
            result = self.parse_file(file_path)
            result["file_path"] = file_path
            results.append(result)
        
        return results
    
    def _parse_file_partially(self, content: str, file_path: Path) -> Dict[str, Any]:
        """
        Attempt partial parsing of a file with syntax errors.
        """
        def try_parse_class_block(class_text: str, class_name: str) -> Tuple[List, List, List, List, List, int]:
            try:
                # Attempt to parse only the class
                class_node = ast.parse(class_text)
                for node in class_node.body:
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        return self._process_class_def(node)
            except:
                pass
            return [], [], [], [], [], 0
        
        # Simple heuristic for extracting classes
        lines = content.split('\n')
        classes = []
        functions = []
        global_vars = []
        class_bases = {}
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('class '):
                # Found class line
                class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                bases = []
                if '(' in line and ')' in line:
                    base_part = line.split('(')[1].split(')')[0]
                    bases = [base.strip() for base in base_part.split(',') if base.strip()]
                
                # Find end of class
                class_lines = [line]
                brace_count = line.count('{') - line.count('}')
                i += 1
                while i < len(lines) and brace_count > 0:
                    class_lines.append(lines[i])
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    i += 1
                
                class_text = '\n'.join(class_lines)
                fields, attributes, static_methods, methods, abstract_method_count = try_parse_class_block(class_text, class_name)
                class_bases[class_name] = bases
                classes.append((
                    class_name,
                    sorted(list(set(fields)), key=lambda x: x[1]),
                    sorted(list(set(attributes)), key=lambda x: x[1]),
                    sorted(list(set(static_methods)), key=lambda x: x[1]),
                    sorted(list(set(methods)), key=lambda x: x[1]),
                    "class",
                    bases
                ))
            elif line.startswith('def '):
                # Found function
                func_name = line.split('def ')[1].split('(')[0].strip()
                functions.append(f"+ {func_name}()")
            i += 1
        
        return {
            "classes": classes,
            "functions": functions,
            "global_vars": global_vars,
            "class_bases": class_bases
        }
    
    def _process_class_def(self, node: ast.ClassDef) -> Tuple[str, List, List, List, List, int]:
        """
        Process a class definition node to extract its components.
        """
        try:
            class_name = node.name
            methods = []
            fields = []
            attributes = []
            abstract_method_count = 0
            static_methods = []
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    try:
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
                        # Skip problematic methods
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
                        # Skip problematic methods
                        continue

                elif isinstance(body_item, ast.ClassDef):
                    # Recursively process nested classes
                    try:
                        # Simply skip nested classes for simplification
                        # In the future, we can add their separate processing
                        pass
                    except Exception as e:
                        # Skip problematic nested classes
                        continue

                elif isinstance(body_item, ast.AnnAssign):
                    try:
                        attributes.extend(self._process_attributes(body_item))
                    except Exception as e:
                        # Skip problematic attributes
                        continue
            return class_name, fields, attributes, static_methods, methods, abstract_method_count
        except Exception as e:
            # Return empty values in case of error
            return "UnknownClass", [], [], [], [], 0
    
    def _process_method_def(self, body_item: ast.FunctionDef) -> Tuple[str, str, bool, bool, bool]:
        """
        Process a method definition node to extract its signature and properties.
        """
        try:
            prefix, vis_type = self._visibility(body_item.name)
            
            # Process regular arguments
            args = [arg.arg for arg in body_item.args.args]
            
            # Determine method type
            is_abstract = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'abstractmethod' for dec in body_item.decorator_list)
            is_static = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'staticmethod' for dec in body_item.decorator_list)
            is_class = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'classmethod' for dec in body_item.decorator_list)
            
            # Remove self/cls from signature for all methods (UML simplification)
            if is_class and args and args[0] == 'cls':
                args = args[1:]
            elif not is_static and not is_class and args and args[0] == 'self':
                args = args[1:]
            
            method_signature = f"{body_item.name}({', '.join(args)})"
            if is_abstract:
                prefix = prefix + ' {abstract}'
            elif is_static:
                prefix = prefix + ' {static}'
            return prefix, method_signature, is_abstract, is_static, is_class
        except Exception as e:
            # Return basic information in case of error
            return '+', f"{body_item.name if hasattr(body_item, 'name') else 'unknown'}()", False, False, False
    
    def _process_attributes(self, body_item: ast.AnnAssign) -> List[Tuple[str, str]]:
        """
        Process attributes of a class defined using type annotations.
        """
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
        """
        Extract type annotation as string.
        """
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
    
    def _process_fields(self, body_item: ast.Assign) -> List[Tuple[str, str]]:
        """
        Process field assignments in class.
        """
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
    
    def _process_function_def(self, node: ast.FunctionDef) -> str:
        """
        Process a function definition node.
        """
        try:
            prefix, vis_type = self._visibility(node.name)
            args = []
            
            for arg in node.args.args:
                arg_name = arg.arg
                if arg.annotation:
                    arg_type = self._get_type_annotation(arg.annotation)
                    args.append(f"{arg_name}: {arg_type}")
                else:
                    args.append(arg_name)
            
            function_signature = f"{prefix} {node.name}({', '.join(args)})"
            return function_signature
        except Exception as e:
            return f"+ {node.name if hasattr(node, 'name') else 'unknown'}()"
    
    def _process_global_vars(self, node: ast.Assign) -> List[Tuple[str, str]]:
        """
        Process global variable assignments.
        """
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
    
    def _determine_class_type(self, has_fields: bool, abstract_method_count: int, total_method_count: int, bases: Optional[List[str]] = None) -> str:
        """
        Determine the type of class based on its characteristics.
        """
        if abstract_method_count > 0:
            return "abstract class"
        elif has_fields and total_method_count == 0:
            return "dataclass"
        elif total_method_count == 0:
            return "interface"
        else:
            return "class"
    
    def _extract_fields_from_init(self, init_method: ast.FunctionDef) -> List[Tuple[str, str]]:
        """
        Extract field assignments from __init__ method.
        """
        try:
            fields = []
            for item in init_method.body:
                if isinstance(item, ast.Assign):
                    fields.extend(self._process_fields(item))
            return fields
        except Exception as e:
            return []
    
    def _extract_documentation(self, node: ast.AST) -> str:
        """
        Extract documentation from AST node.
        """
        try:
            if hasattr(node, 'body') and node.body:
                first_item = node.body[0]
                if isinstance(first_item, ast.Expr) and isinstance(first_item.value, ast.Constant):
                    return first_item.value.value.strip()
            return ""
        except Exception as e:
            return ""
    
    def _visibility(self, name: str) -> Tuple[str, str]:
        """
        Determine the visibility of a member based on its name.
        """
        if name.startswith('__') and name.endswith('__'):
            return '~', 'private'  # Magic
        if name.startswith('__'):
            return '-', 'private'  # Private
        elif name.startswith('_'):
            return '#', 'protected'  # Protected
        else:
            return '+', 'public'  # Public 
    
    def _is_decorator_function(self, node: ast.FunctionDef) -> bool:
        """
        Check if a function is a decorator by analyzing its structure.
        """
        try:
            # Check that function has decorator
            if hasattr(node, 'decorator_list') and node.decorator_list:
                return True
            
            # Check function body structure
            if not node.body:
                return False
            
            # If function contains return func or return wrapper, it's a decorator
            for item in node.body:
                if isinstance(item, ast.Return):
                    if isinstance(item.value, ast.Name):
                        # Check that returned name is a function parameter
                        param_names = [arg.arg for arg in node.args.args]
                        if item.value.id in param_names:
                            # Check that this is not just returning a parameter, but returning a function
                            # If function takes only one parameter and returns it, it's not a decorator
                            if len(node.args.args) == 1 and item.value.id == node.args.args[0].arg:
                                return False
                            # If function returns a parameter that is a function, it's a decorator
                            # But only if it's explicitly a decorator, not a regular function
                            return False  # Let's be less aggressive
                    elif isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Name):
                        # Check that this is not just a function call, but returning a function-parameter
                        if isinstance(item.value.func, ast.Name):
                            param_names = [arg.arg for arg in node.args.args]
                            if item.value.func.id in param_names:
                                return True
                        return False
                elif isinstance(item, ast.FunctionDef):
                    # If function contains a nested function, it might be a decorator
                    return True
            
            return False
        except Exception:
            return False 