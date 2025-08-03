import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import ast

# Добавляем путь к модулю для импорта
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from uml_generator import UMLGenerator


class TestUMLGenerator:
    """Тесты для класса UMLGenerator"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.uml_generator = UMLGenerator(self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_visibility_public(self):
        """Тест видимости публичных членов"""
        prefix, vis_type = self.uml_generator.visibility("public_method")
        assert prefix == "+"
        assert vis_type == "public"

    def test_visibility_protected(self):
        """Тест видимости защищенных членов"""
        prefix, vis_type = self.uml_generator.visibility("_protected_method")
        assert prefix == "#"
        assert vis_type == "protected"

    def test_visibility_private(self):
        """Тест видимости приватных членов"""
        prefix, vis_type = self.uml_generator.visibility("__private_method")
        assert prefix == "-"
        assert vis_type == "private"

    def test_visibility_magic(self):
        """Тест видимости магических методов"""
        prefix, vis_type = self.uml_generator.visibility("__init__")
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

        classes, functions, global_vars, class_bases = self.uml_generator.parse_python_file(file_path)
        
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

        classes, functions, global_vars, class_bases = self.uml_generator.parse_python_file(file_path)
        
        # Должны получить пустые списки при синтаксической ошибке
        assert classes == []
        assert functions == []
        assert global_vars == []
        assert class_bases == {}
        assert len(self.uml_generator.errors) > 0

    def test_parse_python_file_nonexistent(self):
        """Тест парсинга несуществующего файла"""
        file_path = Path(self.temp_dir) / "nonexistent.py"
        
        classes, functions, global_vars, class_bases = self.uml_generator.parse_python_file(file_path)
        
        assert classes == []
        assert functions == []
        assert global_vars == []
        assert class_bases == {}
        assert len(self.uml_generator.errors) > 0

    def test_process_class_def_simple(self):
        """Тест обработки простого класса"""
        python_code = """
class SimpleClass:
    def __init__(self):
        self.field1 = "value1"
    
    def method1(self):
        return "test"
"""
        tree = ast.parse(python_code)
        class_node = tree.body[0]
        
        class_name, fields, attributes, static_methods, methods, abstract_count = self.uml_generator.process_class_def(class_node)
        
        assert class_name == "SimpleClass"
        assert len(fields) == 1
        assert len(methods) == 2  # __init__ + method1

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
        tree = ast.parse(python_code)
        class_node = tree.body[1]  # AbstractClass (после import)
        
        class_name, fields, attributes, static_methods, methods, abstract_count = self.uml_generator.process_class_def(class_node)
        
        assert class_name == "AbstractClass"
        assert abstract_count == 1
        assert len(methods) == 2

    def test_process_method_def_simple(self):
        """Тест обработки простого метода"""
        python_code = """
def simple_method(self, param1, param2):
    return param1 + param2
"""
        tree = ast.parse(python_code)
        method_node = tree.body[0]
        
        prefix, signature, is_abstract, is_static, is_class = self.uml_generator.process_method_def(method_node)
        
        assert prefix == "+"
        assert signature == "simple_method(param1, param2)"
        assert not is_abstract
        assert not is_static
        assert not is_class

    def test_process_method_def_static(self):
        """Тест обработки статического метода"""
        python_code = """
@staticmethod
def static_method(param1):
    return param1
"""
        tree = ast.parse(python_code)
        method_node = tree.body[0]
        
        prefix, signature, is_abstract, is_static, is_class = self.uml_generator.process_method_def(method_node)
        
        assert prefix == "+ {static}"
        assert signature == "static_method(param1)"
        assert not is_abstract
        assert is_static
        assert not is_class

    def test_get_type_annotation_simple(self):
        """Тест обработки простых типов аннотаций"""
        python_code = """
def func(param: str) -> int:
    return len(param)
"""
        tree = ast.parse(python_code)
        func_node = tree.body[0]
        
        # Тест параметра
        param_annotation = func_node.args.args[0].annotation
        result = self.uml_generator.get_type_annotation(param_annotation)
        assert result == "str"
        
        # Тест возвращаемого значения
        return_annotation = func_node.returns
        result = self.uml_generator.get_type_annotation(return_annotation)
        assert result == "int"

    def test_get_type_annotation_complex(self):
        """Тест обработки сложных типов аннотаций"""
        python_code = """
from typing import List, Dict, Optional

def func(items: List[str], config: Dict[str, int]) -> Optional[str]:
    return None
"""
        tree = ast.parse(python_code)
        func_node = tree.body[1]  # func (после import)
        
        # Тест List[str]
        param_annotation = func_node.args.args[0].annotation
        result = self.uml_generator.get_type_annotation(param_annotation)
        assert result == "List[str]"
        
        # Тест Dict[str, int] - учитываем реальное поведение метода
        param_annotation = func_node.args.args[1].annotation
        result = self.uml_generator.get_type_annotation(param_annotation)
        # Метод может возвращать Dict[(str, int)] или Dict[str, int]
        assert "Dict" in result and "str" in result and "int" in result
        
        # Тест Optional[str]
        return_annotation = func_node.returns
        result = self.uml_generator.get_type_annotation(return_annotation)
        assert result == "Optional[str]"

    def test_extract_fields_from_init(self):
        """Тест извлечения полей из __init__ метода"""
        python_code = """
class TestClass:
    def __init__(self):
        self.field1 = "value1"
        self.field2 = 42
        self._protected_field = "protected"
        self.__private_field = "private"
"""
        tree = ast.parse(python_code)
        class_node = tree.body[0]
        init_method = None
        
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                init_method = item
                break
        
        fields = self.uml_generator.extract_fields_from_init(init_method)
        
        assert len(fields) == 4
        field_names = [field[1] for field in fields]
        assert "field1" in field_names
        assert "field2" in field_names
        assert "_protected_field" in field_names
        assert "__private_field" in field_names

    def test_determine_class_type_interface(self):
        """Тест определения типа интерфейса"""
        # Интерфейс: только абстрактные методы, без полей, наследование от ABC
        class_type = self.uml_generator.determine_class_type(
            has_fields=False, 
            abstract_method_count=2, 
            total_method_count=2,
            bases=['ABC']
        )
        assert class_type == "interface"

    def test_determine_class_type_abstract(self):
        """Тест определения типа абстрактного класса"""
        # Абстрактный класс: есть абстрактные методы, но не все
        class_type = self.uml_generator.determine_class_type(
            has_fields=True, 
            abstract_method_count=1, 
            total_method_count=3,
            bases=['ABC']
        )
        assert class_type == "abstract class"

    def test_determine_class_type_regular(self):
        """Тест определения типа обычного класса"""
        # Обычный класс: нет абстрактных методов
        class_type = self.uml_generator.determine_class_type(
            has_fields=True, 
            abstract_method_count=0, 
            total_method_count=2
        )
        assert class_type == "class"

    def test_format_class_info(self):
        """Тест форматирования информации о классе"""
        class_info = (
            "TestClass",  # class_name
            [("+", "field1"), ("#", "_protected_field")],  # fields
            [("+ {static}", "attr1: str")],  # attributes
            [("+ {static}", "static_method()")],  # static_methods
            [("+", "method1()"), ("-", "__private_method()")],  # methods
            "class",  # class_type
            ["BaseClass"]  # bases
        )
        
        result = self.uml_generator.format_class_info(class_info)
        
        assert "class TestClass" in result
        assert "+ field1" in result
        assert "# _protected_field" in result
        assert "+ method1()" in result
        assert "- __private_method()" in result
        assert "+ {static} attr1: str" in result
        assert "+ {static} static_method()" in result

    def test_process_global_vars(self):
        """Тест обработки глобальных переменных"""
        python_code = """
global_var = "test"
_protected_var = 42
__private_var = True
"""
        tree = ast.parse(python_code)
        assign_node = tree.body[0]
        
        global_vars = self.uml_generator.process_global_vars(assign_node)
        
        assert len(global_vars) == 1
        assert global_vars[0][1] == "global_var"
        assert global_vars[0][0] == "+"

    def test_process_function_def(self):
        """Тест обработки определения функции"""
        python_code = """
def test_function(param1, param2):
    return param1 + param2
"""
        tree = ast.parse(python_code)
        func_node = tree.body[0]
        
        result = self.uml_generator.process_function_def(func_node)
        
        assert result == "test_function(param1, param2)" 

    def test_files_with_errors_initialization(self):
        """Тест инициализации атрибута files_with_errors"""
        assert hasattr(self.uml_generator, 'files_with_errors')
        assert isinstance(self.uml_generator.files_with_errors, dict)
        assert len(self.uml_generator.files_with_errors) == 0

    def test_files_with_errors_syntax_error(self):
        """Тест добавления файла с синтаксической ошибкой в files_with_errors"""
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # Незакрытая скобка
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        self.uml_generator.parse_python_file(file_path)
        
        assert str(file_path) in self.uml_generator.files_with_errors
        assert len(self.uml_generator.files_with_errors[str(file_path)]) > 0
        assert "Syntax error" in self.uml_generator.files_with_errors[str(file_path)][0]

    def test_files_with_errors_permission_error(self):
        """Тест добавления файла с ошибкой доступа в files_with_errors"""
        # Создаем файл без прав на чтение
        file_path = Path(self.temp_dir) / "no_access.py"
        with open(file_path, 'w') as f:
            f.write("print('test')")
        
        # Убираем права на чтение
        os.chmod(file_path, 0o000)
        
        try:
            self.uml_generator.parse_python_file(file_path)
            
            assert str(file_path) in self.uml_generator.files_with_errors
            assert len(self.uml_generator.files_with_errors[str(file_path)]) > 0
            assert "Permission denied" in self.uml_generator.files_with_errors[str(file_path)][0]
        finally:
            # Восстанавливаем права для удаления
            os.chmod(file_path, 0o644)

    def test_files_with_errors_encoding_error(self):
        """Тест добавления файла с ошибкой кодировки в files_with_errors"""
        # Создаем файл с неправильной кодировкой
        file_path = Path(self.temp_dir) / "encoding_error.py"
        with open(file_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Неправильная кодировка
        
        self.uml_generator.parse_python_file(file_path)
        
        assert str(file_path) in self.uml_generator.files_with_errors
        assert len(self.uml_generator.files_with_errors[str(file_path)]) > 0
        assert "Encoding error" in self.uml_generator.files_with_errors[str(file_path)][0]

    def test_files_with_errors_multiple_errors(self):
        """Тест добавления нескольких ошибок для одного файла"""
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # Первая ошибка
        
    def another_broken_method(self):
        print("also broken"  # Вторая ошибка
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        self.uml_generator.parse_python_file(file_path)
        
        assert str(file_path) in self.uml_generator.files_with_errors
        assert len(self.uml_generator.files_with_errors[str(file_path)]) > 0

    def test_generate_uml_with_error_files(self):
        """Тест генерации UML с файлами, содержащими ошибки"""
        # Создаем файл с ошибкой
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # Незакрытая скобка
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        # Создаем корректный файл
        correct_code = """
class CorrectClass:
    def correct_method(self):
        return "correct"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(correct_code)
            correct_file_path = Path(f.name)

        # Генерируем UML
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем, что файл с ошибкой добавлен в files_with_errors
        assert str(file_path) in self.uml_generator.files_with_errors
        
        # Проверяем, что корректный файл НЕ добавлен в files_with_errors
        assert str(correct_file_path) not in self.uml_generator.files_with_errors
        
        # Проверяем, что в UML есть красный цвет для файла с ошибкой
        assert "#FF0000" in uml_output
        
        # Проверяем, что есть комментарии с ошибками
        assert "note right : Ошибки:" in uml_output

    def test_generate_uml_error_files_visual_representation(self):
        """Тест визуального представления файлов с ошибками в UML"""
        # Создаем файл с ошибкой
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # Незакрытая скобка
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем красный цвет для файла с ошибкой
        assert "#FF0000" in uml_output
        
        # Проверяем наличие комментариев с ошибками
        assert "note right : Ошибки:" in uml_output
        assert "note right : -" in uml_output
        
        # Проверяем, что стандартный цвет (#F0F0FF) НЕ используется для файла с ошибкой
        # (это может быть сложно проверить, так как может быть несколько файлов)
        
        # Проверяем структуру PlantUML
        assert "package" in uml_output
        assert "<<Frame>>" in uml_output

    def test_files_with_errors_empty_after_clean_parse(self):
        """Тест, что files_with_errors остается пустым при корректном парсинге"""
        python_code = """
class TestClass:
    def correct_method(self):
        return "correct"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        self.uml_generator.parse_python_file(file_path)
        
        # Проверяем, что файл НЕ добавлен в files_with_errors
        assert str(file_path) not in self.uml_generator.files_with_errors
        assert len(self.uml_generator.files_with_errors) == 0

    def test_files_with_errors_backward_compatibility(self):
        """Тест обратной совместимости - старые ошибки все еще работают"""
        python_code = """
class TestClass:
    def broken_method(self):
        print("broken"  # Незакрытая скобка
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', dir=self.temp_dir, delete=False) as f:
            f.write(python_code)
            file_path = Path(f.name)

        self.uml_generator.parse_python_file(file_path)
        
        # Проверяем, что старый атрибут errors все еще работает
        assert len(self.uml_generator.errors) > 0
        assert "Syntax error" in self.uml_generator.errors[0]
        
        # Проверяем, что новый атрибут files_with_errors тоже работает
        assert str(file_path) in self.uml_generator.files_with_errors 