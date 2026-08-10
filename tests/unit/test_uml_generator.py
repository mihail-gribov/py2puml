import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import ast

from py2puml.core.file_filter import FileFilter
from py2puml.core.parser import PythonParser
from py2puml.core.generator import UMLGenerator
from py2puml.core.analyzer import FileAnalyzer


class TestUMLGenerator:
    """Tests for the UMLGenerator class"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)
        self.generator = UMLGenerator(self.temp_dir, self.file_filter)
        self.parser = PythonParser()

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_visibility_public(self):
        """Visibility of public members"""
        prefix, vis_type = self.parser._visibility("public_method")
        assert prefix == "+"
        assert vis_type == "public"

    def test_visibility_protected(self):
        """Visibility of protected members"""
        prefix, vis_type = self.parser._visibility("_protected_method")
        assert prefix == "#"
        assert vis_type == "protected"

    def test_visibility_private(self):
        """Visibility of private members"""
        prefix, vis_type = self.parser._visibility("__private_method")
        assert prefix == "-"
        assert vis_type == "private"

    def test_visibility_magic(self):
        """Visibility of magic methods"""
        prefix, vis_type = self.parser._visibility("__init__")
        assert prefix == "~"
        assert vis_type == "private"

    def test_parse_python_file_valid(self):
        """Parsing a valid Python file"""
        python_code = """
class TestClass:
    def __init__(self):
        self.field1 = "value1"
    
    def test_method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        functions = result["functions"]
        global_vars = result["global_vars"]
        class_bases = result["class_bases"]
        
        assert len(classes) == 1
        assert classes[0][0] == "TestClass"  # class_name
        assert len(classes[0][1]) == 1  # fields
        assert len(classes[0][4]) == 2  # methods (__init__ + test_method)

    def test_parse_python_file_syntax_error(self):
        """Parsing a file with a syntax error"""
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # unclosed parenthesis
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        functions = result["functions"]
        global_vars = result["global_vars"]
        class_bases = result["class_bases"]
        
        # A syntax error must yield empty lists
        assert classes == []
        assert functions == []
        assert global_vars == []
        assert class_bases == {}
        assert len(self.parser.errors) > 0

    def test_parse_python_file_nonexistent(self):
        """Parsing a missing file"""
        file_path = Path(self.temp_dir) / "nonexistent.py"
        
        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        functions = result["functions"]
        global_vars = result["global_vars"]
        class_bases = result["class_bases"]
        
        assert classes == []
        assert functions == []
        assert global_vars == []
        assert class_bases == {}
        assert len(self.parser.errors) > 0

    def test_process_class_def_simple(self):
        """Processing a simple class definition"""
        python_code = """
class SimpleClass:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        assert class_info[0] == "SimpleClass"  # name
        assert len(class_info[1]) == 1  # fields
        assert len(class_info[4]) == 2  # methods

    def test_process_class_def_abstract(self):
        """Processing an abstract class"""
        python_code = """
from abc import ABC, abstractmethod

class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass
    
    def concrete_method(self):
        return "concrete"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        assert class_info[0] == "AbstractClass"  # name
        assert class_info[6] == "abstract"  # class_type

    def test_process_method_def_simple(self):
        """Processing a simple method definition"""
        python_code = """
class TestClass:
    def simple_method(self, param1, param2):
        return param1 + param2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        methods = class_info[4]  # methods
        assert len(methods) == 1
        assert "simple_method" in methods[0][1]  # method signature

    def test_process_method_def_static(self):
        """Processing a static method"""
        python_code = """
class TestClass:
    @staticmethod
    def static_method(param):
        return param
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        static_methods = class_info[3]  # static_methods
        assert len(static_methods) == 1
        assert "static_method" in static_methods[0][1]  # method signature

    def test_get_type_annotation_simple(self):
        """Reading a simple type annotation"""
        python_code = """
class TestClass:
    field: str = "value"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        attributes = class_info[2]  # attributes
        assert len(attributes) == 1

    def test_get_type_annotation_complex(self):
        """Reading a complex type annotation"""
        python_code = """
from typing import List, Dict

class TestClass:
    field: List[Dict[str, int]] = []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        attributes = class_info[2]  # attributes
        assert len(attributes) == 1

    def test_extract_fields_from_init(self):
        """Extracting fields from __init__"""
        python_code = """
class TestClass:
    def __init__(self):
        self.field1 = "value1"
        self.field2 = "value2"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        fields = class_info[1]  # fields
        assert len(fields) == 2

    def test_determine_class_type_interface(self):
        """Detecting an interface class type"""
        python_code = """
class InterfaceClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        assert class_info[6] == "interface"  # class_type

    def test_determine_class_type_abstract(self):
        """Detecting an abstract class type"""
        python_code = """
from abc import ABC, abstractmethod

class AbstractClass(ABC):
    @abstractmethod
    def method(self):
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        assert class_info[6] == "abstract"  # class_type

    def test_determine_class_type_regular(self):
        """Detecting a regular class type"""
        python_code = """
class RegularClass:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        classes = result["classes"]
        
        assert len(classes) == 1
        class_info = classes[0]
        assert class_info[6] == "class"  # class_type

    def test_format_class_info(self):
        """Formatting class information"""
        class_info = (
            "TestClass",  # name
            [("+", "field1")],  # fields
            [],  # attributes
            [],  # static_methods
            [("+", "method()")],  # methods
            [],  # properties
            "class",  # class_type
            []  # bases
        )
        
        formatted = self.generator._format_class_info(class_info)
        assert 'class "TestClass"' in formatted
        assert "+ field1" in formatted
        assert "+ method()" in formatted

    def test_process_global_vars(self):
        """Processing global variables"""
        python_code = """
GLOBAL_VAR = "value"
ANOTHER_VAR = 42
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        global_vars = result["global_vars"]
        
        assert len(global_vars) == 2
        var_names = [var[1] for var in global_vars]
        assert "GLOBAL_VAR" in var_names
        assert "ANOTHER_VAR" in var_names

    def test_process_function_def(self):
        """Processing a function definition"""
        python_code = """
def global_function(param1, param2):
    return param1 + param2
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        functions = result["functions"]
        
        assert len(functions) == 1
        assert "global_function" in functions[0]

    def test_files_with_errors_initialization(self):
        """Error list initialisation"""
        assert hasattr(self.parser, 'errors')
        assert hasattr(self.parser, 'files_with_errors')
        assert isinstance(self.parser.errors, list)
        assert isinstance(self.parser.files_with_errors, dict)

    def test_files_with_errors_syntax_error(self):
        """Handling syntax errors"""
        python_code = """
class TestClass:
    def broken_method(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        
        assert len(self.parser.errors) > 0
        assert str(file_path) in self.parser.files_with_errors

    def test_files_with_errors_permission_error(self):
        """Handling permission errors"""
        # Create a file that cannot be read
        file_path = Path(self.temp_dir) / "no_access.py"
        with open(file_path, 'w') as f:
            f.write("class Test: pass")
        
        # Drop read permissions
        os.chmod(file_path, 0o000)
        
        try:
            result = self.parser.parse_file(file_path)
            assert len(self.parser.errors) > 0
        finally:
            # Restore permissions
            os.chmod(file_path, 0o644)

    def test_files_with_errors_encoding_error(self):
        """Handling encoding errors"""
        # Create a file with an invalid encoding
        file_path = Path(self.temp_dir) / "bad_encoding.py"
        with open(file_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # invalid encoding
        
        result = self.parser.parse_file(file_path)
        assert len(self.parser.errors) > 0

    def test_files_with_errors_multiple_errors(self):
        """Handling multiple errors"""
        python_code = """
class TestClass:
    def method1(self:
        pass
    
    def method2(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        
        assert len(self.parser.errors) > 0
        assert str(file_path) in self.parser.files_with_errors
        assert len(self.parser.files_with_errors[str(file_path)]) > 0

    def test_generate_uml_with_error_files(self):
        """UML generation with files containing errors"""
        # Create a file containing an error
        python_code = """
class TestClass:
    def broken_method(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert len(self.generator.errors) > 0

    def test_generate_uml_error_files_visual_representation(self):
        """Visual representation of files with errors"""
        # Create a file containing an error
        python_code = """
class TestClass:
    def broken_method(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        # A file with errors must be marked red
        assert "#FF0000" in uml_output
        assert "note right : Errors:" in uml_output

    def test_files_with_errors_empty_after_clean_parse(self):
        """No errors after a clean parse"""
        python_code = """
class TestClass:
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        result = self.parser.parse_file(Path(f.name))
        
        # A clean parse must leave no errors
        assert len(self.parser.errors) == 0
        assert len(self.parser.files_with_errors) == 0

    def test_files_with_errors_backward_compatibility(self):
        """Backward compatibility of error reporting"""
        python_code = """
class TestClass:
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        result = self.parser.parse_file(Path(f.name))
        
        # The result structure must stay compatible
        assert "classes" in result
        assert "functions" in result
        assert "global_vars" in result
        assert "class_bases" in result 