import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from py2puml.core.file_filter import FileFilter
from py2puml.core.generator import UMLGenerator


class TestOutputFormat:
    """Тесты для форматов вывода"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)
        self.generator = UMLGenerator(self.temp_dir, self.file_filter)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plantuml_format_generation(self):
        """Тест генерации PlantUML формата"""
        python_code = """
class TestClass:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert "class TestClass" in uml_output
        assert "method()" in uml_output

    def test_plantuml_package_structure(self):
        """Test package structure in PlantUML"""
        # Create directory structure
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        # File in root directory
        root_code = """
class RootClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(root_code)

        # File in subdirectory
        sub_code = """
class SubClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=subdir, delete=False) as f:
            f.write(sub_code)

        uml_output = self.generator.generate_uml()
        
        assert "package" in uml_output
        assert "RootClass" in uml_output
        assert "SubClass" in uml_output

    def test_plantuml_inheritance(self):
        """Test inheritance in PlantUML"""
        python_code = """
class BaseClass:
    pass

class ChildClass(BaseClass):
    pass

class GrandChildClass(ChildClass):
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "BaseClass" in uml_output
        assert "ChildClass" in uml_output
        assert "GrandChildClass" in uml_output
        assert "<|--" in uml_output  # Inheritance

    def test_plantuml_methods_and_fields(self):
        """Test methods and fields in PlantUML"""
        python_code = """
class TestClass:
    field1: str = "value1"
    field2: int = 42
    
    def __init__(self):
        self.instance_field = "instance"
    
    def public_method(self):
        return "public"
    
    def _protected_method(self):
        return "protected"
    
    def __private_method(self):
        return "private"
    
    @staticmethod
    def static_method():
        return "static"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "+ public_method()" in uml_output
        assert "# _protected_method()" in uml_output
        assert "- __private_method()" in uml_output
        assert "{static} static_method()" in uml_output
        assert "+ field1: str" in uml_output
        assert "+ field2: int" in uml_output

    def test_plantuml_abstract_classes(self):
        """Test abstract classes in PlantUML"""
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

        uml_output = self.generator.generate_uml()
        
        assert "abstract class AbstractClass" in uml_output
        assert "{abstract} abstract_method()" in uml_output
        assert "concrete_method()" in uml_output

    def test_plantuml_interfaces(self):
        """Тест интерфейсов в PlantUML"""
        python_code = """
class InterfaceClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "interface InterfaceClass" in uml_output

    def test_plantuml_global_functions(self):
        """Тест глобальных функций в PlantUML"""
        python_code = """
def global_function():
    return "global"

class TestClass:
    def method(self):
        return "method"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "global_function()" in uml_output
        assert "TestClass" in uml_output

    def test_plantuml_global_variables(self):
        """Тест глобальных переменных в PlantUML"""
        python_code = """
GLOBAL_VAR = "value"
ANOTHER_VAR = 42

class TestClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "GLOBAL_VAR" in uml_output
        assert "ANOTHER_VAR" in uml_output

    def test_plantuml_error_handling(self):
        """Тест обработки ошибок в PlantUML"""
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

    def test_plantuml_error_visualization(self):
        """Тест визуализации ошибок в PlantUML"""
        python_code = """
class TestClass:
    def broken_method(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        # Check red color for files with errors
        assert "#FF0000" in uml_output
        assert "note right : Ошибки:" in uml_output

    def test_plantuml_complex_structure(self):
        """Test complex structure in PlantUML"""
        python_code = """
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass

class ConcreteClass(BaseClass):
    field1: str = "value1"
    field2: int = 42
    
    def __init__(self):
        self.instance_field = "instance"
    
    def abstract_method(self):
        return "implemented"
    
    def concrete_method(self, param: str) -> bool:
        return True
    
    @staticmethod
    def static_method() -> str:
        return "static"

def global_function(param: int) -> str:
    return str(param)

GLOBAL_VAR = "global"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "abstract class BaseClass" in uml_output
        assert "class ConcreteClass" in uml_output
        assert "global_function(param: int)" in uml_output
        assert "GLOBAL_VAR" in uml_output
        assert "<|--" in uml_output  # Inheritance

    def test_plantuml_empty_directory(self):
        """Test empty directory in PlantUML"""
        uml_output = self.generator.generate_uml()
        
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert "note right : Директория пуста" in uml_output

    def test_plantuml_gitignore_filtering(self):
        """Test .gitignore filtering in PlantUML"""
        # Create .gitignore
        gitignore_content = """
*.pyc
__pycache__/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        # Create files
        normal_code = """
class NormalClass:
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(normal_code)

        # Create file that should be ignored
        ignored_file = Path(self.temp_dir) / "ignored.pyc"
        ignored_file.touch()

        uml_output = self.generator.generate_uml()
        
        assert "NormalClass" in uml_output
        assert "ignored.pyc" not in uml_output

    def test_plantuml_encoding_handling(self):
        """Test encoding handling in PlantUML"""
        python_code = """
# -*- coding: utf-8 -*-
class TestClass:
    def method(self):
        return "тест"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "TestClass" in uml_output
        assert "method()" in uml_output

    def test_plantuml_special_characters(self):
        """Тест специальных символов в PlantUML"""
        python_code = """
class TestClass:
    def method_with_underscores(self):
        return "test"
    
    def method_with_dashes(self):
        return "test"
    
    def method_with_numbers_123(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        assert "method_with_underscores()" in uml_output
        assert "method_with_dashes()" in uml_output
        assert "method_with_numbers_123()" in uml_output 