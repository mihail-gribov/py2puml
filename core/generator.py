import os
from pathlib import Path
from typing import Dict, List, Any

from .file_filter import FileFilter
from .parser import PythonParser, CLASS_STYLE_CONFIG


class UMLGenerator:
    """
    Handles generation of UML diagrams from Python source code.
    """
    
    def __init__(self, directory_path: str, file_filter: FileFilter):
        """
        Initialize UML generator.
        
        Args:
            directory_path: Path to the directory containing Python files
            file_filter: FileFilter instance for filtering files
        """
        self.directory = Path(directory_path)
        self.file_filter = file_filter
        self.parser = PythonParser()
        self.uml = '@startuml\n'
        self.all_class_bases = {}
        self.errors = []  # List for storing errors
        self.files_with_errors = {}  # Dictionary for storing files with errors
    
    def generate_uml(self) -> str:
        """
        Generate UML for all Python files in the specified directory.
        
        Returns:
            PlantUML diagram as string
        """
        try:
            # Check directory existence
            if not self.directory.exists():
                error_msg = f"Directory not found: {self.directory}"
                self.errors.append(error_msg)
                print(f"Error: {error_msg}")
                return "@startuml\n@enduml"
            
            # Check directory read permissions
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
                return "@startuml\nnote right : Директория пуста\n@enduml"
                
        except Exception as e:
            error_msg = f"Error scanning directory {self.directory}: {e}"
            self.errors.append(error_msg)
            print(f"Error: {error_msg}")
            return "@startuml\n@enduml"
        
        for path in pathlist:
            try:
                relative_path = path.relative_to(self.directory).with_suffix('')
                package_name = str(relative_path).replace('/', '.').replace('\\', '.')  # Handle paths for both Windows and Unix
                
                # Parse file
                parsed_data = self.parser.parse_file(path)
                class_infos = parsed_data["classes"]
                function_infos = parsed_data["functions"]
                global_vars = parsed_data["global_vars"]
                class_bases = parsed_data["class_bases"]

                # Pass errors from parser to generator
                self.errors.extend(self.parser.errors)
                self.files_with_errors.update(self.parser.files_with_errors)

                self.all_class_bases.update(class_bases)
                
                # Check if there are errors in this file
                file_has_errors = str(path) in self.parser.files_with_errors
                
                if file_has_errors:
                    # File with errors - red color and special icon
                    self.uml += f'package "{package_name}" <<Frame>> #FF0000 {{\n'
                    # Add comment with error descriptions
                    self.uml += f'  note right : Ошибки:\n'
                    for error in self.parser.files_with_errors[str(path)]:
                        self.uml += f'  note right : - {error}\n'
                else:
                    # Regular file - standard color
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
        """
        Format the information of a class for UML representation.
        
        Args:
            class_info: Tuple containing class information
            
        Returns:
            Formatted class string for UML
        """
        try:
            class_name, fields, attributes, static_methods, methods, properties, class_type, bases = class_info
            
            # Get style configuration for the class type
            style_config = CLASS_STYLE_CONFIG.get(class_type, CLASS_STYLE_CONFIG["class"])
            keyword = style_config["keyword"]
            color = style_config["color"]
            
            # Format class declaration with optional background color
            if color:
                class_str = f"  {keyword} \"{class_name}\" << (C,{color}) >> {{\n"
            else:
                class_str = f"  {keyword} \"{class_name}\" {{\n"
            
            # Process fields
            for prefix, field in fields:
                try:
                    class_str += f"    {prefix} {field}\n"
                except Exception as e:
                    # Skip problematic fields
                    continue
                    
            if len(fields) and (len(methods) or len(properties)):
                class_str += "    ....\n"

            # Process properties
            for prefix, property_info in properties:
                try:
                    class_str += f"    {prefix} {property_info}\n"
                except Exception as e:
                    # Skip problematic properties
                    continue

            # Process methods
            for prefix, method in methods:
                try:
                    class_str += f"    {prefix} {method}\n"
                except Exception as e:
                    # Skip problematic methods
                    continue

            if (len(fields) or len(methods) or len(properties)) and (len(attributes) or len(static_methods)):
                class_str += "    __Static__\n"

            # Process attributes
            for prefix, attribute in attributes:
                try:
                    class_str += f"    {prefix} {attribute}\n"
                except Exception as e:
                    # Skip problematic attributes
                    continue

            if len(attributes) and len(static_methods):
                class_str += "    ....\n"

            # Process static methods
            for prefix, method in static_methods:
                try:
                    class_str += f"    {prefix} {method}\n"
                except Exception as e:
                    # Skip problematic static methods
                    continue

            class_str += "  }\n"
            return class_str
        except Exception as e:
            # Return basic information in case of error
            class_name = class_info[0] if len(class_info) > 0 else 'UnknownClass'
            return f"  class {class_name} {{\n  }}\n"
    
    def _add_inheritance_relations(self):
        """
        Add inheritance relationships between classes to the UML.
        """
        for class_name, bases in self.all_class_bases.items():
            for base in bases:
                self.uml += f"{base} <|-- {class_name}\n" 