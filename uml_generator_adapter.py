"""
Adapter for backward compatibility with old tests.
This module provides the old UMLGenerator interface using the new architecture.
"""

from py2puml.core.file_filter import FileFilter
from py2puml.core.generator import UMLGenerator as NewUMLGenerator
from py2puml.core.parser import PythonParser


class UMLGenerator:
    """
    Backward compatibility adapter for old tests.
    This class provides the same interface as the old UMLGenerator.
    """
    
    def __init__(self, directory_path, use_gitignore=True):
        """
        Initialize UML generator with backward compatibility.
        
        Args:
            directory_path: Path to the directory containing Python files
            use_gitignore: Whether to use .gitignore patterns for filtering
        """
        self.directory = directory_path
        self.use_gitignore = use_gitignore
        self.file_filter = FileFilter(directory_path, use_gitignore=use_gitignore)
        self.generator = NewUMLGenerator(directory_path, self.file_filter)
        self.parser = PythonParser()
        
        # Backward compatibility attributes
        self.errors = []
        self.files_with_errors = {}
        self.uml = '@startuml\n'
        self.all_class_bases = {}
    
    def visibility(self, name):
        """
        Determine the visibility of a member based on its name.
        """
        return self.parser._visibility(name)
    
    def parse_python_file(self, file_path):
        """
        Parse a Python file to extract class and function definitions, global variables, and class inheritance.
        """
        result = self.parser.parse_file(file_path)
        
        # Update errors for backward compatibility
        self.errors.extend(self.parser.errors)
        self.files_with_errors.update(self.parser.files_with_errors)
        
        return (
            result["classes"],
            result["functions"],
            result["global_vars"],
            result["class_bases"]
        )
    
    def generate_uml(self):
        """
        Generate UML for all Python files in the specified directory.
        """
        return self.generator.generate_uml()
    
    def describe_file(self, file_path, format='text', include_docs=True):
        """
        Describe a Python file with classes, functions, and variables.
        """
        from py2puml.core.analyzer import FileAnalyzer
        
        analyzer = FileAnalyzer(str(file_path.parent))
        return analyzer.describe_file(file_path, format=format, include_docs=include_docs)
    
    # Backward compatibility methods that were in the old UMLGenerator
    def _load_gitignore_patterns(self):
        """Backward compatibility method."""
        pass
    
    def _should_ignore(self, file_path):
        """Backward compatibility method."""
        return self.file_filter.should_ignore(file_path)
    
    def _should_ignore_pathspec(self, file_path):
        """Backward compatibility method."""
        return self.file_filter._should_ignore_pathspec(file_path)
    
    def _should_ignore_simple(self, file_path):
        """Backward compatibility method."""
        return self.file_filter._should_ignore_simple(file_path)
    
    def _load_simple_gitignore_patterns(self, gitignore_file):
        """Backward compatibility method."""
        return self.file_filter._load_simple_gitignore_patterns(gitignore_file)
    
    def _match_simple_pattern(self, file_path, pattern):
        """Backward compatibility method."""
        return self.file_filter._match_simple_pattern(file_path, pattern)
    
    def _parse_file_partially(self, content, file_path):
        """Backward compatibility method."""
        return self.parser._parse_file_partially(content, file_path)
    
    def _process_ast_node(self, node, classes, functions, global_vars, class_bases, file_path):
        """Backward compatibility method."""
        # This method is not directly available in the new parser
        # We'll implement a simplified version
        pass
    
    def extract_fields_from_init(self, init_method):
        """Backward compatibility method."""
        return self.parser._extract_fields_from_init(init_method)
    
    def process_class_def(self, node):
        """Backward compatibility method."""
        return self.parser._process_class_def(node)
    
    def process_method_def(self, body_item):
        """Backward compatibility method."""
        return self.parser._process_method_def(body_item)
    
    def process_attributes(self, body_item):
        """Backward compatibility method."""
        return self.parser._process_attributes(body_item)
    
    def get_type_annotation(self, annotation):
        """Backward compatibility method."""
        return self.parser._get_type_annotation(annotation)
    
    def process_fields(self, body_item):
        """Backward compatibility method."""
        return self.parser._process_fields(body_item)
    
    def process_function_def(self, node):
        """Backward compatibility method."""
        return self.parser._process_function_def(node)
    
    def determine_class_type(self, has_fields, abstract_method_count, total_method_count, bases=None):
        """Backward compatibility method."""
        return self.parser._determine_class_type(has_fields, abstract_method_count, total_method_count, bases)
    
    def format_class_info(self, class_info):
        """Backward compatibility method."""
        return self.generator._format_class_info(class_info)
    
    def add_inheritance_relations(self):
        """Backward compatibility method."""
        return self.generator._add_inheritance_relations()
    
    def process_global_vars(self, node):
        """Backward compatibility method."""
        return self.parser._process_global_vars(node)
    
    def _extract_documentation(self, node):
        """Backward compatibility method."""
        return self.parser._extract_documentation(node)
    
    def _get_file_summary(self, file_path, classes, functions, variables):
        """Backward compatibility method."""
        from py2puml.core.analyzer import FileAnalyzer
        analyzer = FileAnalyzer(str(file_path.parent))
        return analyzer._get_file_summary(file_path, classes, functions, variables) 