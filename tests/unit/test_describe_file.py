import pytest
import tempfile
import os
from pathlib import Path
from uml_generator import UMLGenerator


class TestDescribeFile:
    """Тесты для функциональности describe_file."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.temp_dir = tempfile.mkdtemp()
        self.uml_generator = UMLGenerator(self.temp_dir, use_gitignore=False)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content, filename="test.py"):
        """Создает тестовый файл с заданным содержимым."""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_simple_file_parsing(self):
        """Тест парсинга простого файла."""
        content = '''
"""Module for testing."""
from typing import List, Dict

# Global variables
API_VERSION = "v1.0"
DEFAULT_TIMEOUT = 30

class User:
    """User data model."""
    
    def __init__(self, name: str):
        """Initialize user."""
        self.name = name
    
    def get_name(self) -> str:
        """Get user name."""
        return self.name

def create_user(name: str) -> User:
    """Create a new user."""
    return User(name)

# Type aliases
UserList = List[User]
'''
        
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "File: " in result
        assert "Summary: " in result
        assert "Classes:" in result
        assert "Functions:" in result
        assert "Variables:" in result
        assert "User" in result
        assert "create_user" in result
        assert "API_VERSION" in result
    
    def test_empty_file(self):
        """Тест парсинга пустого файла."""
        content = ""
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "File: " in result
        assert "Summary: 0 lines, 0 classes, 0 functions, 0 variables" in result
        assert "Classes:" not in result
        assert "Functions:" not in result
        assert "Variables:" not in result
    
    def test_file_with_only_comments(self):
        """Тест файла только с комментариями."""
        content = '''
# This is a comment
# Another comment

# Empty lines above
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "File: " in result
        assert "Summary: " in result
        assert "0 classes, 0 functions, 0 variables" in result
    
    def test_class_documentation_extraction(self):
        """Тест извлечения документации из классов."""
        content = '''
class MyClass:
    """This is a sample class with documentation."""
    
    def __init__(self):
        """Initialize the class."""
        pass
    
    def method1(self):
        """Sample method."""
        pass
    
    def _private_method(self):
        """Private method."""
        pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "MyClass" in result
        assert "This is a sample class with documentation" in result
        assert "Initialize the class" in result
        assert "Sample method" in result
        assert "Private method" in result
    
    def test_function_documentation_extraction(self):
        """Тест извлечения документации из функций."""
        content = '''
def global_function():
    """Global function documentation."""
    pass

async def async_function():
    """Async function documentation."""
    pass

@decorator
def decorated_function():
    """Decorated function documentation."""
    pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "global_function" in result
        assert "Global function documentation" in result
        assert "async_function" in result
        assert "Async function documentation" in result
        assert "decorated_function" in result
        assert "Decorated function documentation" in result
    
    def test_various_docstring_styles(self):
        """Тест различных стилей документации."""
        content = '''
def google_style_func(param1: str, param2: int) -> bool:
    """Google style docstring.
    
    Args:
        param1: First parameter
        param2: Second parameter
        
    Returns:
        Boolean result
    """
    pass

def numpy_style_func(values):
    """NumPy style docstring.
    
    Parameters
    ----------
    values : array_like
        Input array
        
    Returns
    -------
    float
        Mean value
    """
    pass

def rest_style_func(text):
    """reST style docstring.
    
    :param text: Input string
    :type text: str
    :return: Processed result
    :rtype: str
    """
    pass

def simple_docstring():
    """Simple one-line docstring."""
    pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "Google style docstring" in result
        assert "NumPy style docstring" in result
        assert "reST style docstring" in result
        assert "Simple one-line docstring" in result
    
    def test_json_format(self):
        """Тест JSON формата вывода."""
        content = '''
class TestClass:
    """Test class."""
    
    def test_method(self):
        """Test method."""
        pass

def test_function():
    """Test function."""
    pass

TEST_VAR = "test"
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path, format='json')
        
        import json
        data = json.loads(result)
        
        assert data['file'] == str(file_path)
        assert 'summary' in data
        assert 'classes' in data
        assert 'functions' in data
        assert 'variables' in data
        assert len(data['classes']) == 1
        assert len(data['functions']) == 1
        assert len(data['variables']) == 1
    
    def test_yaml_format(self):
        """Тест YAML формата вывода."""
        content = '''
class TestClass:
    """Test class."""
    pass

def test_function():
    """Test function."""
    pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path, format='yaml')
        
        # Проверяем, что это валидный YAML
        try:
            import yaml
            data = yaml.safe_load(result)
            assert data['file'] == str(file_path)
            assert 'summary' in data
            assert 'classes' in data
            assert 'functions' in data
        except ImportError:
            # PyYAML не установлен, проверяем сообщение об ошибке
            assert "PyYAML library not available" in result
    
    def test_no_docs_flag(self):
        """Тест флага --no-docs."""
        content = '''
class TestClass:
    """This should be excluded."""
    
    def test_method(self):
        """This should be excluded."""
        pass

def test_function():
    """This should be excluded."""
    pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path, include_docs=False)
        
        assert "TestClass" in result
        assert "test_method" in result
        assert "test_function" in result
        assert "This should be excluded" not in result
    
    def test_syntax_error_handling(self):
        """Тест обработки синтаксических ошибок."""
        content = '''
class TestClass:
    def test_method(self):
        # Неправильный синтаксис
        if True
            pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        # Должен обработать ошибку gracefully и вернуть результат
        assert "File: " in result
        assert "Summary: " in result
        # Проверяем, что есть предупреждения об ошибках
        assert len(self.uml_generator.errors) > 0
    
    def test_file_not_found(self):
        """Тест обработки несуществующего файла."""
        non_existent_file = Path(self.temp_dir) / "non_existent.py"
        result = self.uml_generator.describe_file(non_existent_file)
        
        assert "Error:" in result
        assert "not found" in result.lower()
    
    def test_inheritance_classes(self):
        """Тест классов с наследованием."""
        content = '''
from abc import ABC, abstractmethod

class BaseClass:
    """Base class."""
    pass

class AbstractClass(ABC):
    """Abstract base class."""
    
    @abstractmethod
    def abstract_method(self):
        """Abstract method."""
        pass

class ConcreteClass(BaseClass):
    """Concrete class inheriting from BaseClass."""
    
    def concrete_method(self):
        """Concrete method."""
        pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "BaseClass" in result
        assert "AbstractClass" in result
        assert "ConcreteClass" in result
        assert "Bases: ABC" in result
        assert "Bases: BaseClass" in result
        assert "abstract class" in result.lower()
    
    def test_decorators(self):
        """Тест функций с декораторами."""
        content = '''
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def decorated_function():
    """Decorated function."""
    pass

class TestClass:
    @staticmethod
    def static_method():
        """Static method."""
        pass
    
    @classmethod
    def class_method(cls):
        """Class method."""
        pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "decorated_function" in result
        assert "static_method" in result
        assert "class_method" in result
        assert "Decorated function" in result
        assert "Static method" in result
        assert "Class method" in result
    
    def test_async_functions(self):
        """Тест async функций."""
        content = '''
import asyncio

async def async_function():
    """Async function."""
    pass

class TestClass:
    async def async_method(self):
        """Async method."""
        pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "async_function" in result
        assert "async_method" in result
        assert "Async function" in result
        assert "Async method" in result
    
    def test_type_annotations(self):
        """Тест типизации."""
        content = '''
from typing import List, Dict, Optional

def typed_function(param1: str, param2: int = 10) -> bool:
    """Typed function."""
    pass

class TypedClass:
    def __init__(self, name: str):
        self.name: str = name
    
    def get_data(self) -> List[Dict[str, str]]:
        """Get typed data."""
        pass

# Type aliases
UserDict = Dict[str, str]
OptionalUser = Optional[TypedClass]
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "typed_function" in result
        assert "TypedClass" in result
        assert "UserDict" in result
        assert "OptionalUser" in result
        assert "Typed function" in result
        assert "Get typed data" in result
    
    def test_complex_signatures(self):
        """Тест сложных сигнатур."""
        content = '''
def complex_function(
    param1: str,
    param2: int = 10,
    *args,
    **kwargs
) -> bool:
    """Function with complex signature."""
    pass

def function_with_defaults(
    required: str,
    optional: int = 42,
    flag: bool = True
) -> str:
    """Function with default values."""
    pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "complex_function" in result
        assert "function_with_defaults" in result
        assert "Function with complex signature" in result
        assert "Function with default values" in result
    
    def test_special_characters(self):
        """Тест специальных символов в именах."""
        content = '''
class TestClass123:
    """Class with numbers."""
    pass

def function_with_underscores():
    """Function with underscores."""
    pass

def unicode_function():
    """Function with unicode."""
    pass

# Variables with special names
test_var_123 = "test"
_private_var = "private"
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "TestClass123" in result
        assert "function_with_underscores" in result
        assert "unicode_function" in result
        assert "test_var_123" in result
        assert "_private_var" in result
    
    def test_nested_classes(self):
        """Тест вложенных классов."""
        content = '''
class OuterClass:
    """Outer class."""
    
    class InnerClass:
        """Inner class."""
        
        def inner_method(self):
            """Inner method."""
            pass
    
    def outer_method(self):
        """Outer method."""
        pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "OuterClass" in result
        # Вложенные классы пока не обрабатываются
        # assert "InnerClass" in result
        assert "Outer class" in result
        assert "outer_method" in result
        assert "Outer method" in result
    
    def test_unsupported_format(self):
        """Тест неподдерживаемого формата."""
        content = '''
def test_function():
    """Test function."""
    pass
'''
        file_path = self.create_test_file(content)
        
        # Проверяем, что ValueError выбрасывается
        with pytest.raises(ValueError, match="Unsupported format"):
            self.uml_generator.describe_file(file_path, format='unsupported')
    
    def test_multiline_docstrings(self):
        """Тест многострочных docstrings."""
        content = '''
class TestClass:
    """This is a multiline docstring.
    
    It has multiple lines and should be properly extracted.
    
    Args:
        None
        
    Returns:
        None
    """
    
    def test_method(self):
        """Another multiline docstring.
        
        With more details and formatting.
        """
        pass
'''
        file_path = self.create_test_file(content)
        result = self.uml_generator.describe_file(file_path)
        
        assert "This is a multiline docstring" in result
        assert "Another multiline docstring" in result
        assert "With more details and formatting" in result 