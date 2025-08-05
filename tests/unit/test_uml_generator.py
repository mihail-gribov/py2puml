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
    """Тесты для класса UMLGenerator"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)
        self.generator = UMLGenerator(self.temp_dir, self.file_filter)
        self.parser = PythonParser()

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_visibility_public(self):
        """Тест видимости публичных членов"""
        prefix, vis_type = self.parser._visibility("public_method")
        assert prefix == "+"
        assert vis_type == "public"

    def test_visibility_protected(self):
        """Тест видимости защищенных членов"""
        prefix, vis_type = self.parser._visibility("_protected_method")
        assert prefix == "#"
        assert vis_type == "protected"

    def test_visibility_private(self):
        """Тест видимости приватных членов"""
        prefix, vis_type = self.parser._visibility("__private_method")
        assert prefix == "-"
        assert vis_type == "private"

    def test_visibility_magic(self):
        """Тест видимости магических методов"""
        prefix, vis_type = self.parser._visibility("__init__")
        assert prefix == "~"
        assert vis_type == "private"

    def test_parse_python_file_valid(self):
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
        classes = result["classes"]
        functions = result["functions"]
        global_vars = result["global_vars"]
        class_bases = result["class_bases"]
        
        assert len(classes) == 1
        assert classes[0][0] == "TestClass"  # class_name
        assert len(classes[0][1]) == 1  # fields
        assert len(classes[0][4]) == 2  # methods (__init__ + test_method)

    def test_parse_python_file_syntax_error(self):
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
        classes = result["classes"]
        functions = result["functions"]
        global_vars = result["global_vars"]
        class_bases = result["class_bases"]
        
        # Должны получить пустые списки при синтаксической ошибке
        assert classes == []
        assert functions == []
        assert global_vars == []
        assert class_bases == {}
        assert len(self.parser.errors) > 0

    def test_parse_python_file_nonexistent(self):
        """Тест парсинга несуществующего файла"""
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
        """Тест обработки простого определения класса"""
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
        """Тест обработки абстрактного класса"""
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
        assert class_info[5] == "abstract class"  # class_type

    def test_process_method_def_simple(self):
        """Тест обработки простого определения метода"""
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
        """Тест обработки статического метода"""
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
        """Тест получения простой аннотации типа"""
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
        """Тест получения сложной аннотации типа"""
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
        """Тест извлечения полей из __init__"""
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
        """Тест определения типа класса как интерфейса"""
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
        assert class_info[5] == "interface"  # class_type

    def test_determine_class_type_abstract(self):
        """Тест определения типа класса как абстрактного"""
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
        assert class_info[5] == "abstract class"  # class_type

    def test_determine_class_type_regular(self):
        """Тест определения типа класса как обычного"""
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
        assert class_info[5] == "class"  # class_type

    def test_format_class_info(self):
        """Тест форматирования информации о классе"""
        class_info = (
            "TestClass",  # name
            [("+", "field1")],  # fields
            [],  # attributes
            [],  # static_methods
            [("+", "method()")],  # methods
            "class",  # class_type
            []  # bases
        )
        
        formatted = self.generator._format_class_info(class_info)
        assert "class TestClass" in formatted
        assert "+ field1" in formatted
        assert "+ method()" in formatted

    def test_process_global_vars(self):
        """Тест обработки глобальных переменных"""
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
        """Тест обработки определения функции"""
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
        """Тест инициализации списка ошибок"""
        assert hasattr(self.parser, 'errors')
        assert hasattr(self.parser, 'files_with_errors')
        assert isinstance(self.parser.errors, list)
        assert isinstance(self.parser.files_with_errors, dict)

    def test_files_with_errors_syntax_error(self):
        """Тест обработки синтаксических ошибок"""
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
        """Тест обработки ошибок доступа"""
        # Создаем файл без прав на чтение
        file_path = Path(self.temp_dir) / "no_access.py"
        with open(file_path, 'w') as f:
            f.write("class Test: pass")
        
        # Убираем права на чтение
        os.chmod(file_path, 0o000)
        
        try:
            result = self.parser.parse_file(file_path)
            assert len(self.parser.errors) > 0
        finally:
            # Восстанавливаем права
            os.chmod(file_path, 0o644)

    def test_files_with_errors_encoding_error(self):
        """Тест обработки ошибок кодировки"""
        # Создаем файл с неправильной кодировкой
        file_path = Path(self.temp_dir) / "bad_encoding.py"
        with open(file_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Неправильная кодировка
        
        result = self.parser.parse_file(file_path)
        assert len(self.parser.errors) > 0

    def test_files_with_errors_multiple_errors(self):
        """Тест обработки множественных ошибок"""
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
        """Тест генерации UML с файлами с ошибками"""
        # Создаем файл с ошибкой
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
        """Тест визуального представления файлов с ошибками"""
        # Создаем файл с ошибкой
        python_code = """
class TestClass:
    def broken_method(self:
        pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        uml_output = self.generator.generate_uml()
        
        # Проверяем, что файл с ошибкой отмечен красным цветом
        assert "#FF0000" in uml_output
        assert "note right : Ошибки:" in uml_output

    def test_files_with_errors_empty_after_clean_parse(self):
        """Тест пустых ошибок после чистого парсинга"""
        python_code = """
class TestClass:
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        result = self.parser.parse_file(Path(f.name))
        
        # После чистого парсинга ошибок быть не должно
        assert len(self.parser.errors) == 0
        assert len(self.parser.files_with_errors) == 0

    def test_files_with_errors_backward_compatibility(self):
        """Тест обратной совместимости с ошибками"""
        python_code = """
class TestClass:
    def method(self):
        return "test"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)

        result = self.parser.parse_file(Path(f.name))
        
        # Проверяем, что структура результата совместима
        assert "classes" in result
        assert "functions" in result
        assert "global_vars" in result
        assert "class_bases" in result 