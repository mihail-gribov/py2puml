import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional


# Configuration for class type styling
CLASS_STYLE_CONFIG = {
    "class": {
        "keyword": "class",
        "color": None,  # Standard color
        "stereotype": None
    },
    "abstract": {
        "keyword": "abstract", 
        "color": "#FFFFFF",  # White
        "stereotype": None
    },
    "dataclass": {
        "keyword": "class",
        "color": "#90EE90",  # Light green
        "stereotype": None
    },
    "interface": {
        "keyword": "interface",
        "color": "#FFFFFF",  # White
        "stereotype": None
    }
}


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
        def try_parse_class_block(class_text: str, class_name: str) -> Tuple[List, List, List, List, List, List, int]:
            try:
                # Attempt to parse only the class
                class_node = ast.parse(class_text)
                for node in class_node.body:
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        return self._process_class_def(node)
            except:
                pass
            return [], [], [], [], [], [], 0
        
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
                fields, attributes, static_methods, methods, properties, abstract_method_count = try_parse_class_block(class_text, class_name)
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
            return class_name, fields, attributes, static_methods, methods, properties, abstract_method_count
        except Exception as e:
            # Return empty values in case of error
            return "UnknownClass", [], [], [], [], [], 0
    
    def _process_method_def(self, body_item: ast.FunctionDef) -> Tuple[str, str, bool, bool, bool]:
        """
        Process a method definition node to extract its signature and properties.
        """
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
            
            # Process regular arguments
            args = [arg.arg for arg in body_item.args.args]
            
            # Remove self/cls from signature for all methods (UML simplification)
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
    
    def _determine_class_type(self, has_fields: bool, abstract_method_count: int, total_method_count: int, bases: Optional[List[str]] = None, decorators: Optional[List[str]] = None) -> str:
        """
        Determine the type of class based on its characteristics and decorators.
        """
        # Check for dataclass decorator first
        if decorators and 'dataclass' in decorators:
            return "dataclass"
        
        if abstract_method_count > 0:
            return "abstract"
        elif has_fields and total_method_count == 0:
            return "dataclass"
        elif total_method_count == 0:
            return "interface"
        else:
            return "class"
    
    def get_class_style(self, class_type: str) -> Dict[str, Any]:
        """
        Get style configuration for a class type.
        
        Args:
            class_type: The type of class (class, abstract, dataclass, interface)
            
        Returns:
            Dictionary containing style configuration
        """
        return CLASS_STYLE_CONFIG.get(class_type, CLASS_STYLE_CONFIG["class"])
    
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
        Excludes dataclass decorator since it's handled by styling.
        """
        if not decorators:
            return name
        
        # Filter out dataclass decorator since it's handled by styling
        filtered_decorators = [d for d in decorators if d != 'dataclass']
        
        if not filtered_decorators:
            return name
        
        # Sort decorators for consistent output
        sorted_decorators = sorted(filtered_decorators)
        decorator_suffix = "".join(f"@{d}" for d in sorted_decorators)
        return f"{name}{decorator_suffix}"
    
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
    
    def _is_property_method(self, node: ast.FunctionDef) -> bool:
        """
        Check if a method is a property (has @property decorator).
        Only the main @property method should be processed, not @property.setter or @property.deleter.
        """
        try:
            if hasattr(node, 'decorator_list') and node.decorator_list:
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'property':
                        return True
            return False
        except Exception:
            return False
    
    def _is_property_setter_or_deleter(self, node: ast.FunctionDef) -> bool:
        """
        Check if a method is a property setter or deleter (has @property.setter or @property.deleter decorator).
        These methods should not be processed as regular methods.
        """
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
        """
        Process a property method to determine its access level and return property info.
        """
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
        """
        Check if the property getter raises AttributeError (indicating write-only property).
        """
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