import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from py2puml.core.file_filter import FileFilter
from py2puml.core.parser import PythonParser
from py2puml.core.generator import UMLGenerator
from py2puml.core.analyzer import FileAnalyzer


class TestEdgeCases:
    """Tests for edge cases"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)
        self.generator = UMLGenerator(self.temp_dir, self.file_filter)
        self.parser = PythonParser()
        self.analyzer = FileAnalyzer(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_file(self):
        """Empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write("")
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []

    def test_file_with_only_comments(self):
        """File containing only comments"""
        python_code = """
# This is a comment
# Another comment
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []

    def test_file_with_only_whitespace(self):
        """File containing only whitespace"""
        python_code = """
    
    
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []

    def test_file_with_unicode_characters(self):
        """File with Unicode identifiers"""
        python_code = """
class ТестКласс:
    def метод(self):
        return "тест"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1
        assert result["classes"][0][0] == "ТестКласс"

    def test_file_with_special_characters_in_names(self):
        """File with special characters in names"""
        python_code = """
class TestClass_123:
    def method_with_underscores(self):
        return "test"
    
    def method_with_dashes(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1
        assert result["classes"][0][0] == "TestClass_123"

    def test_file_with_very_long_names(self):
        """File with very long names"""
        long_name = "A" * 1000
        python_code = f"""
class {long_name}:
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1
        assert result["classes"][0][0] == long_name

    def test_file_with_nested_classes(self):
        """File with nested classes"""
        python_code = """
class OuterClass:
    class InnerClass:
        def method(self):
            return "inner"
    
    def outer_method(self):
        return "outer"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1
        assert result["classes"][0][0] == "OuterClass"

    def test_file_with_multiple_inheritance(self):
        """File with multiple inheritance"""
        python_code = """
class Base1:
    pass

class Base2:
    pass

class Child(Base1, Base2):
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 3

    def test_file_with_complex_decorators(self):
        """File with complex decorators"""
        python_code = """
def decorator1(func):
    return func

def decorator2(param):
    def wrapper(func):
        return func
    return wrapper

@decorator1
@decorator2("param")
def decorated_function():
    return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["functions"]) == 1

    def test_file_with_async_await(self):
        """File using async/await"""
        python_code = """
import asyncio

async def async_function():
    await asyncio.sleep(1)
    return "async"

class TestClass:
    async def async_method(self):
        await asyncio.sleep(1)
        return "async method"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["functions"]) == 1
        assert len(result["classes"]) == 1

    def test_file_with_type_annotations(self):
        """File with type annotations"""
        python_code = """
from typing import List, Dict, Optional, Union, Tuple

def typed_function(param: str) -> Optional[str]:
    return param

class TestClass:
    field: str = "value"
    
    def method(self, param: int) -> bool:
        return True
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["functions"]) == 1
        assert len(result["classes"]) == 1

    def test_file_with_f_strings(self):
        """File using f-strings"""
        python_code = """
name = "World"
greeting = f"Hello, {name}!"

class TestClass:
    def method(self):
        return f"Hello, {name}!"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1

    def test_file_with_walrus_operator(self):
        """File using the walrus operator (:=)"""
        python_code = """
def test_walrus():
    if (n := len([1, 2, 3])) > 2:
        return n
    return 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["functions"]) == 1

    def test_file_with_match_statement(self):
        """File using a match statement (Python 3.10+)"""
        python_code = """
def test_match(value):
    match value:
        case 1:
            return "one"
        case 2:
            return "two"
        case _:
            return "other"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["functions"]) == 1

    def test_file_with_very_large_content(self):
        """File with very large content"""
        # Create a large file
        large_content = "class TestClass:\n"
        for i in range(1000):
            large_content += f"    def method_{i}(self):\n        return {i}\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(large_content)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1
        assert len(result["classes"][0][4]) == 1000  # 1000 methods

    def test_file_with_mixed_encodings(self):
        """File with mixed encodings"""
        python_code = """
# -*- coding: utf-8 -*-
class TestClass:
    def method(self):
        return "тест"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1

    def test_file_with_syntax_errors(self):
        """File with syntax errors"""
        python_code = """
class TestClass:
    def broken_method(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 0
        assert len(self.parser.errors) > 0

    def test_file_with_import_errors(self):
        """File with import errors"""
        python_code = """
from nonexistent_module import nonexistent_function

class TestClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(result["classes"]) == 1

    def test_file_with_circular_imports(self):
        """File with circular imports"""
        # Create two files with circular imports
        file1_content = """
from test_file2 import ClassB

class ClassA:
    def method(self):
        return ClassB()
"""
        file2_content = """
from test_file1 import ClassA

class ClassB:
    def method(self):
        return ClassA()
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(file1_content)
            file1_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(file2_content)
            file2_path = Path(f.name)

        result1 = self.parser.parse_file(file1_path)
        result2 = self.parser.parse_file(file2_path)
        
        assert len(result1["classes"]) == 1
        assert len(result2["classes"]) == 1

    def test_file_with_unicode_errors(self):
        """File with Unicode errors"""
        # Create a file with an invalid encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(b'\xff\xfe\x00\x00')  # invalid encoding
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        assert len(self.parser.errors) > 0

    def test_file_with_permission_errors(self):
        """File with permission errors"""
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

    def test_empty_directory(self):
        """Empty directory"""
        uml_output = self.generator.generate_uml()
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert "note right : Directory is empty" in uml_output

    def test_directory_with_only_non_python_files(self):
        """Directory with non-Python files only"""
        # Create non-Python files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', dir=self.temp_dir, delete=False) as f:
            f.write("This is a text file")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', dir=self.temp_dir, delete=False) as f:
            f.write("# This is a markdown file")

        uml_output = self.generator.generate_uml()
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert "note right : Directory is empty" in uml_output

    def test_directory_with_hidden_files(self):
        """Directory with hidden files"""
        # Create a hidden Python file
        hidden_file = Path(self.temp_dir) / ".hidden.py"
        with open(hidden_file, 'w') as f:
            f.write("class HiddenClass: pass")

        # Create a regular Python file
        normal_file = Path(self.temp_dir) / "normal.py"
        with open(normal_file, 'w') as f:
            f.write("class NormalClass: pass")

        uml_output = self.generator.generate_uml()
        assert "NormalClass" in uml_output
        assert "HiddenClass" not in uml_output  # hidden files are ignored

    def test_directory_with_symlinks(self):
        """Directory with symbolic links"""
        # Create the original file
        original_file = Path(self.temp_dir) / "original.py"
        with open(original_file, 'w') as f:
            f.write("class OriginalClass: pass")

        # Create a symbolic link
        symlink_file = Path(self.temp_dir) / "symlink.py"
        try:
            symlink_file.symlink_to(original_file)
        except OSError:
            # Symlinks may be unsupported on some systems
            pytest.skip("Symbolic links not supported on this system")

        uml_output = self.generator.generate_uml()
        assert "OriginalClass" in uml_output 