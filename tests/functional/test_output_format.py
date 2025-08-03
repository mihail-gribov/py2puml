import pytest
import tempfile
import re
from pathlib import Path

# Добавляем путь к модулю для импорта
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from uml_generator import UMLGenerator


class TestOutputFormat:
    """Функциональные тесты для проверки формата выходных данных"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.uml_generator = UMLGenerator(self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plantuml_syntax_validity(self):
        """Тест корректности PlantUML синтаксиса"""
        # Создаем тестовый файл
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("""
class TestClass:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"
""")
        
        # Генерируем UML
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем базовую структуру PlantUML
        assert uml_output.startswith("@startuml")
        assert uml_output.endswith("@enduml")
        
        # Проверяем наличие пакета
        assert 'package "test"' in uml_output
        
        # Проверяем наличие класса
        assert "class TestClass" in uml_output

    def test_class_visibility_representation(self):
        """Тест представления видимости классов"""
        test_file = Path(self.temp_dir) / "visibility.py"
        test_file.write_text("""
class TestClass:
    def __init__(self):
        self.public_field = "public"
        self._protected_field = "protected"
        self.__private_field = "private"
    
    def public_method(self):
        return "public"
    
    def _protected_method(self):
        return "protected"
    
    def __private_method(self):
        return "private"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем видимость полей
        assert "+ public_field" in uml_output
        assert "# _protected_field" in uml_output
        assert "- __private_field" in uml_output
        
        # Проверяем видимость методов
        assert "+ public_method()" in uml_output
        assert "# _protected_method()" in uml_output
        assert "- __private_method()" in uml_output

    def test_inheritance_relationships(self):
        """Тест отношений наследования"""
        test_file = Path(self.temp_dir) / "inheritance.py"
        test_file.write_text("""
class BaseClass:
    def base_method(self):
        return "base"

class DerivedClass(BaseClass):
    def derived_method(self):
        return "derived"

class AnotherDerived(BaseClass):
    def another_method(self):
        return "another"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем отношения наследования
        assert "BaseClass <|-- DerivedClass" in uml_output
        assert "BaseClass <|-- AnotherDerived" in uml_output

    def test_static_methods_and_attributes(self):
        """Тест статических методов и атрибутов"""
        test_file = Path(self.temp_dir) / "static.py"
        test_file.write_text("""
class TestClass:
    static_attr: str = "static"
    
    def __init__(self):
        self.instance_field = "instance"
    
    @staticmethod
    def static_method():
        return "static"
    
    def instance_method(self):
        return "instance"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем статические атрибуты
        assert "+ {static} static_attr: str" in uml_output
        
        # Проверяем статические методы
        assert "+ {static} static_method()" in uml_output
        
        # Проверяем разделитель статических элементов
        assert "__Static__" in uml_output

    def test_abstract_classes_and_interfaces(self):
        """Тест абстрактных классов и интерфейсов"""
        test_file = Path(self.temp_dir) / "abstract.py"
        test_file.write_text("""
from abc import ABC, abstractmethod

class AbstractClass(ABC):
    def __init__(self):
        self.field = "value"
    
    @abstractmethod
    def abstract_method(self):
        pass
    
    def concrete_method(self):
        return "concrete"

class Interface(ABC):
    @abstractmethod
    def method1(self):
        pass
    
    @abstractmethod
    def method2(self):
        pass
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем абстрактный класс
        assert "abstract class AbstractClass" in uml_output
        assert "+ {abstract} abstract_method()" in uml_output
        
        # Проверяем интерфейс
        assert "interface Interface" in uml_output
        assert "+ {abstract} method1()" in uml_output
        assert "+ {abstract} method2()" in uml_output

    def test_global_variables_and_functions(self):
        """Тест глобальных переменных и функций"""
        test_file = Path(self.temp_dir) / "globals.py"
        test_file.write_text("""
# Глобальные переменные
GLOBAL_CONSTANT = "constant"
_protected_global = "protected"
__private_global = "private"

# Глобальные функции
def global_function():
    return "global"

def _protected_function():
    return "protected"

def __private_function():
    return "private"

class TestClass:
    def method(self):
        return "test"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем глобальные переменные
        assert 'class "Global Variables"' in uml_output
        assert "+ GLOBAL_CONSTANT" in uml_output
        assert "# _protected_global" in uml_output
        assert "- __private_global" in uml_output
        
        # Проверяем глобальные функции
        assert 'class "global_function()"' in uml_output
        assert 'class "_protected_function()"' in uml_output
        assert 'class "__private_function()"' in uml_output

    def test_complex_type_annotations(self):
        """Тест сложных типов аннотаций"""
        test_file = Path(self.temp_dir) / "types.py"
        test_file.write_text("""
from typing import List, Dict, Optional, Union, Tuple

class TestClass:
    def __init__(self):
        self.simple_field: str = "simple"
        self.list_field: List[str] = []
        self.dict_field: Dict[str, int] = {}
        self.optional_field: Optional[str] = None
        self.union_field: Union[str, int] = "test"
        self.tuple_field: Tuple[str, int] = ("test", 42)
    
    def method_with_types(self, param1: str, param2: List[int]) -> Optional[bool]:
        return True
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем простые типы
        assert "+ {static} simple_field: str" in uml_output
        
        # Проверяем сложные типы
        assert "+ {static} list_field: List[str]" in uml_output
        assert "+ {static} dict_field: Dict[str, int]" in uml_output
        assert "+ {static} optional_field: Optional[str]" in uml_output
        assert "+ {static} union_field: Union[str, int]" in uml_output
        assert "+ {static} tuple_field: Tuple[str, int]" in uml_output
        
        # Проверяем методы с типами
        assert "method_with_types(param1, param2)" in uml_output

    def test_package_structure(self):
        """Тест структуры пакетов"""
        # Создаем структуру пакетов
        package_dir = Path(self.temp_dir) / "package"
        package_dir.mkdir()
        
        subpackage_dir = package_dir / "subpackage"
        subpackage_dir.mkdir()
        
        # Файл в корневом пакете
        main_file = package_dir / "main.py"
        main_file.write_text("""
class MainClass:
    def main_method(self):
        return "main"
""")
        
        # Файл в подпакете
        sub_file = subpackage_dir / "sub.py"
        sub_file.write_text("""
class SubClass:
    def sub_method(self):
        return "sub"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем структуру пакетов
        assert 'package "package.main"' in uml_output
        assert 'package "package.subpackage.sub"' in uml_output
        assert "class MainClass" in uml_output
        assert "class SubClass" in uml_output

    def test_method_parameters(self):
        """Тест параметров методов"""
        test_file = Path(self.temp_dir) / "methods.py"
        test_file.write_text("""
class TestClass:
    def simple_method(self):
        return "simple"
    
    def method_with_params(self, param1, param2, *args, **kwargs):
        return "complex"
    
    def method_with_defaults(self, param1="default", param2=None):
        return "defaults"
    
    def method_with_types(self, param1: str, param2: int = 0) -> bool:
        return True
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем методы с разными типами параметров
        assert "simple_method()" in uml_output
        assert "method_with_params(param1, param2)" in uml_output
        assert "method_with_defaults(param1, param2)" in uml_output
        assert "method_with_types(param1, param2)" in uml_output

    def test_error_handling_in_output(self):
        """Тест обработки ошибок в выходных данных"""
        test_file = Path(self.temp_dir) / "broken.py"
        test_file.write_text("""
class ValidClass:
    def valid_method(self):
        return "valid"

class BrokenClass:
    def broken_method(self):
        print("broken"  # Синтаксическая ошибка
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем, что валидный класс обработан
        assert "class ValidClass" in uml_output
        assert "valid_method()" in uml_output
        
        # Проверяем, что сломанный класс пропущен
        assert "class BrokenClass" not in uml_output
        
        # Проверяем наличие ошибок
        assert len(self.uml_generator.errors) > 0

    def test_empty_project_output(self):
        """Тест выходных данных для пустого проекта"""
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем минимальную валидную структуру
        assert uml_output.startswith("@startuml")
        assert uml_output.endswith("@enduml")
        
        # Проверяем, что нет лишнего содержимого
        lines = uml_output.split('\n')
        assert len(lines) == 2  # Только @startuml и @enduml

    def test_large_project_structure(self):
        """Тест структуры большого проекта"""
        # Создаем множество файлов
        for i in range(10):
            test_file = Path(self.temp_dir) / f"module_{i}.py"
            test_file.write_text(f"""
class Class{i}:
    def method_{i}(self):
        return {i}
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем наличие всех классов
        for i in range(10):
            assert f"class Class{i}" in uml_output
            assert f"method_{i}()" in uml_output
        
        # Проверяем структуру пакетов
        for i in range(10):
            assert f'package "module_{i}"' in uml_output

    def test_plantuml_syntax_completeness(self):
        """Тест полноты PlantUML синтаксиса"""
        test_file = Path(self.temp_dir) / "complete.py"
        test_file.write_text("""
from abc import ABC, abstractmethod
from typing import List, Optional

class BaseClass:
    def base_method(self):
        return "base"

class DerivedClass(BaseClass):
    def __init__(self):
        self.field = "value"
    
    def derived_method(self):
        return "derived"

class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self):
        pass

class Interface(ABC):
    @abstractmethod
    def method1(self):
        pass
    
    @abstractmethod
    def method2(self):
        pass

class ComplexClass:
    static_attr: str = "static"
    
    def __init__(self):
        self.instance_field: int = 42
        self._protected_field = "protected"
        self.__private_field = "private"
    
    @staticmethod
    def static_method():
        return "static"
    
    def instance_method(self, param1: str, param2: Optional[int] = None) -> bool:
        return True
    
    def _protected_method(self):
        return "protected"
    
    def __private_method(self):
        return "private"

# Глобальные переменные
GLOBAL_CONSTANT = "constant"
_protected_global = "protected"

# Глобальные функции
def global_function():
    return "global"

def _protected_function():
    return "protected"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем все элементы PlantUML синтаксиса
        assert "@startuml" in uml_output
        assert "@enduml" in uml_output
        assert 'package "complete"' in uml_output
        
        # Проверяем классы
        assert "class BaseClass" in uml_output
        assert "class DerivedClass" in uml_output
        assert "abstract class AbstractClass" in uml_output
        assert "interface Interface" in uml_output
        assert "class ComplexClass" in uml_output
        
        # Проверяем отношения наследования
        assert "BaseClass <|-- DerivedClass" in uml_output
        
        # Проверяем поля и методы
        assert "+ field" in uml_output
        assert "+ {static} static_attr: str" in uml_output
        assert "+ {static} instance_field: int" in uml_output
        assert "# _protected_field" in uml_output
        assert "- __private_field" in uml_output
        
        # Проверяем методы
        assert "+ {static} static_method()" in uml_output
        assert "+ instance_method(param1, param2)" in uml_output
        assert "# _protected_method()" in uml_output
        assert "- __private_method()" in uml_output
        
        # Проверяем глобальные элементы
        assert 'class "Global Variables"' in uml_output
        assert "+ GLOBAL_CONSTANT" in uml_output
        assert "# _protected_global" in uml_output
        assert 'class "global_function()"' in uml_output
        assert 'class "_protected_function()"' in uml_output 