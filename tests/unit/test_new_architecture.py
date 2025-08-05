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
    """Тесты для класса FileFilter"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_should_ignore_disabled(self):
        """Тест отключенной фильтрации"""
        file_filter = FileFilter(self.temp_dir, use_gitignore=False)
        file_path = Path(self.temp_dir) / "test.py"
        assert not file_filter.should_ignore(file_path)

    def test_should_ignore_without_gitignore(self):
        """Тест фильтрации без .gitignore файла"""
        file_path = Path(self.temp_dir) / "test.py"
        assert not self.file_filter.should_ignore(file_path)

    def test_should_ignore_with_gitignore(self):
        """Тест фильтрации с .gitignore файлом"""
        # Создаем .gitignore файл
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n__pycache__/\n")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Файл, который должен быть проигнорирован
        ignored_file = Path(self.temp_dir) / "test.pyc"
        assert file_filter.should_ignore(ignored_file)
        
        # Файл, который не должен быть проигнорирован
        normal_file = Path(self.temp_dir) / "test.py"
        assert not file_filter.should_ignore(normal_file)


class TestPythonParser:
    """Тесты для класса PythonParser"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = PythonParser()

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_file_valid(self):
        """Тест парсинга корректного Python файла"""
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
        """Тест парсинга файла с синтаксической ошибкой"""
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # Незакрытая скобка
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        result = self.parser.parse_file(file_path)
        
        # Должны получить пустые списки при синтаксической ошибке
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []
        assert result["class_bases"] == {}
        assert len(self.parser.errors) > 0

    def test_parse_file_nonexistent(self):
        """Тест парсинга несуществующего файла"""
        file_path = Path(self.temp_dir) / "nonexistent.py"
        
        result = self.parser.parse_file(file_path)
        
        assert result["classes"] == []
        assert result["functions"] == []
        assert result["global_vars"] == []
        assert result["class_bases"] == {}
        assert len(self.parser.errors) > 0

    def test_visibility_methods(self):
        """Тест методов определения видимости"""
        # Публичные
        prefix, vis_type = self.parser._visibility("public_method")
        assert prefix == "+"
        assert vis_type == "public"

        # Защищенные
        prefix, vis_type = self.parser._visibility("_protected_method")
        assert prefix == "#"
        assert vis_type == "protected"

        # Приватные
        prefix, vis_type = self.parser._visibility("__private_method")
        assert prefix == "-"
        assert vis_type == "private"

        # Магические
        prefix, vis_type = self.parser._visibility("__init__")
        assert prefix == "~"
        assert vis_type == "private"


class TestUMLGenerator:
    """Тесты для класса UMLGenerator"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)
        self.generator = UMLGenerator(self.temp_dir, self.file_filter)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_uml_empty_directory(self):
        """Тест генерации UML для пустой директории"""
        uml_output = self.generator.generate_uml()
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output

    def test_generate_uml_with_files(self):
        """Тест генерации UML с файлами"""
        # Создаем Python файл
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
        """Тест форматирования информации о классе"""
        class_info = (
            "TestClass",  # name
            [("+", "field1")],  # fields
            [],  # attributes
            [],  # static_methods
            [("+", "test_method()")],  # methods
            "class",  # class_type
            []  # bases
        )
        
        formatted = self.generator._format_class_info(class_info)
        assert "class TestClass" in formatted
        assert "+ field1" in formatted
        assert "+ test_method()" in formatted

    def test_add_inheritance_relations(self):
        """Тест добавления отношений наследования"""
        self.generator.all_class_bases = {
            "ChildClass": ["ParentClass"],
            "GrandChildClass": ["ChildClass"]
        }
        
        # Проверяем, что UML содержит отношения наследования
        self.generator._add_inheritance_relations()
        assert "ParentClass <|-- ChildClass" in self.generator.uml
        assert "ChildClass <|-- GrandChildClass" in self.generator.uml


class TestFileAnalyzer:
    """Тесты для класса FileAnalyzer"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = FileAnalyzer(self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_describe_file_text_format(self):
        """Тест описания файла в текстовом формате"""
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
        """Тест описания файла в JSON формате"""
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
        """Тест описания файла в YAML формате"""
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
        """Тест описания несуществующего файла"""
        file_path = Path(self.temp_dir) / "nonexistent.py"
        result = self.analyzer.describe_file(file_path)
        assert "Error:" in result

    def test_describe_file_invalid_format(self):
        """Тест описания файла с неверным форматом"""
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
        """Тест получения сводки файла"""
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