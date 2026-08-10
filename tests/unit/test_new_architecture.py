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


class TestFileFilter:
    """Tests for the FileFilter class"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_should_ignore_disabled(self):
        """Disabled filtering"""
        file_filter = FileFilter(self.temp_dir, use_gitignore=False)
        file_path = Path(self.temp_dir) / "test.py"
        assert not file_filter.should_ignore(file_path)

    def test_should_ignore_without_gitignore(self):
        """Filtering without a .gitignore file"""
        file_path = Path(self.temp_dir) / "test.py"
        assert not self.file_filter.should_ignore(file_path)

    def test_should_ignore_with_gitignore(self):
        """Filtering with a .gitignore file"""
        # Create a .gitignore file
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n__pycache__/\n")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # A file that must be ignored
        ignored_file = Path(self.temp_dir) / "test.pyc"
        assert file_filter.should_ignore(ignored_file)
        
        # A file that must not be ignored
        normal_file = Path(self.temp_dir) / "test.py"
        assert not file_filter.should_ignore(normal_file)


class TestPythonParser:
    """Tests for the PythonParser class"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = PythonParser()

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_file_valid(self):
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
        
        assert len(result["classes"]) == 1
        assert result["classes"][0][0] == "TestClass"  # class_name
        assert len(result["classes"][0][1]) == 1  # fields
        assert len(result["classes"][0][4]) == 2  # methods (__init__ + test_method)

    def test_parse_file_syntax_error(self):
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
        
        # A syntax error must yield empty lists
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []
        assert result["class_bases"] == {}
        assert len(self.parser.errors) > 0

    def test_parse_file_nonexistent(self):
        """Parsing a missing file"""
        file_path = Path(self.temp_dir) / "nonexistent.py"
        
        result = self.parser.parse_file(file_path)
        
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []
        assert result["class_bases"] == {}
        assert len(self.parser.errors) > 0

    def test_visibility_methods(self):
        """Visibility detection methods"""
        # public
        prefix, vis_type = self.parser._visibility("public_method")
        assert prefix == "+"
        assert vis_type == "public"

        # protected
        prefix, vis_type = self.parser._visibility("_protected_method")
        assert prefix == "#"
        assert vis_type == "protected"

        # private
        prefix, vis_type = self.parser._visibility("__private_method")
        assert prefix == "-"
        assert vis_type == "private"

        # magic
        prefix, vis_type = self.parser._visibility("__init__")
        assert prefix == "~"
        assert vis_type == "private"


class TestUMLGenerator:
    """Tests for the UMLGenerator class"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)
        self.generator = UMLGenerator(self.temp_dir, self.file_filter)

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_uml_empty_directory(self):
        """UML generation for an empty directory"""
        uml_output = self.generator.generate_uml()
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output

    def test_generate_uml_with_files(self):
        """UML generation with files"""
        # Create a Python file
        python_code = """
class TestClass:
    def __init__(self):
        self.field1 = "value1"
    
    def test_method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert "TestClass" in uml_output

    def test_format_class_info(self):
        """Formatting class information"""
        class_info = (
            "TestClass",  # name
            [("+", "field1")],  # fields
            [],  # attributes
            [],  # static_methods
            [("+", "test_method()")],  # methods
            [],  # properties
            "class",  # class_type
            []  # bases
        )
        
        formatted = self.generator._format_class_info(class_info)
        assert 'class "TestClass"' in formatted
        assert "+ field1" in formatted
        assert "+ test_method()" in formatted

    def test_add_inheritance_relations(self):
        """Adding inheritance relationships"""
        self.generator.all_class_bases = {
            "ChildClass": ["ParentClass"],
            "GrandChildClass": ["ChildClass"]
        }
        
        # The UML must contain inheritance relationships
        self.generator._add_inheritance_relations()
        assert "ParentClass <|-- ChildClass" in self.generator.uml
        assert "ChildClass <|-- GrandChildClass" in self.generator.uml


class TestFileAnalyzer:
    """Tests for the FileAnalyzer class"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = FileAnalyzer(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_describe_file_text_format(self):
        """Describing a file as text"""
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

        result = self.analyzer.describe_file(file_path, format='text')
        assert "File:" in result
        assert "TestClass" in result
        assert "test_method" in result

    def test_describe_file_json_format(self):
        """Describing a file as JSON"""
        python_code = """
class TestClass:
    def test_method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.analyzer.describe_file(file_path, format='json')
        import json
        data = json.loads(result)
        assert data["file"] == str(file_path)
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "TestClass"

    def test_describe_file_yaml_format(self):
        """Describing a file as YAML"""
        python_code = """
class TestClass:
    def test_method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.analyzer.describe_file(file_path, format='yaml')
        import yaml
        data = yaml.safe_load(result)
        assert data["file"] == str(file_path)
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "TestClass"

    def test_describe_file_nonexistent(self):
        """Describing a missing file"""
        file_path = Path(self.temp_dir) / "nonexistent.py"
        result = self.analyzer.describe_file(file_path)
        assert "Error:" in result

    def test_describe_file_invalid_format(self):
        """Describing a file with an invalid format"""
        python_code = """
class TestClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        with pytest.raises(ValueError):
            self.analyzer.describe_file(file_path, format='invalid')

    def test_get_file_summary(self):
        """Getting a file summary"""
        python_code = """
class TestClass:
    def test_method(self):
        return "test"

def test_function():
    return "function"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        classes = [("TestClass", [], [], [], [], "class", [])]
        functions = ["+ test_function()"]
        variables = []

        summary = self.analyzer._get_file_summary(file_path, classes, functions, variables)
        assert summary["classes"] == 1
        assert summary["functions"] == 1
        assert summary["variables"] == 0
        assert summary["lines"] > 0 