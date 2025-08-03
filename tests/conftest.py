import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_directory():
    """Фикстура для создания временной директории"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_file(temp_directory):
    """Фикстура для создания образцового Python файла"""
    test_file = temp_directory / "sample.py"
    test_file.write_text("""
class SampleClass:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"
""")
    return test_file


@pytest.fixture
def complex_python_file(temp_directory):
    """Фикстура для создания сложного Python файла"""
    test_file = temp_directory / "complex.py"
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
    return test_file


@pytest.fixture
def broken_python_file(temp_directory):
    """Фикстура для создания Python файла с ошибками"""
    test_file = temp_directory / "broken.py"
    test_file.write_text("""
class ValidClass:
    def valid_method(self):
        return "valid"

class BrokenClass:
    def broken_method(self):
        print("broken"  # Синтаксическая ошибка
""")
    return test_file


@pytest.fixture
def empty_directory(temp_directory):
    """Фикстура для пустой директории"""
    return temp_directory


@pytest.fixture
def project_structure(temp_directory):
    """Фикстура для создания структуры проекта"""
    # Создаем структуру проекта
    project_dir = temp_directory / "project"
    project_dir.mkdir()
    
    subpackage_dir = project_dir / "subpackage"
    subpackage_dir.mkdir()
    
    # Основной модуль
    main_file = project_dir / "main.py"
    main_file.write_text("""
from .utils import Helper
from .models import User

class Application:
    def __init__(self):
        self.helper = Helper()
        self.users = []
    
    def run(self):
        return "running"
""")
    
    # Модуль утилит
    utils_file = project_dir / "utils.py"
    utils_file.write_text("""
class Helper:
    def __init__(self):
        self.data = {}
    
    def help(self):
        return "helping"
""")
    
    # Модуль моделей
    models_file = project_dir / "models.py"
    models_file.write_text("""
class User:
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
""")
    
    # Файл в подпакете
    sub_file = subpackage_dir / "sub.py"
    sub_file.write_text("""
class SubClass:
    def sub_method(self):
        return "sub"
""")
    
    return project_dir 