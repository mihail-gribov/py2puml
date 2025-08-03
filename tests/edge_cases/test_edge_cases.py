import pytest
import tempfile
import os
from pathlib import Path

# Добавляем путь к модулю для импорта
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from uml_generator import UMLGenerator


class TestEdgeCases:
    """Тесты граничных случаев"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.uml_generator = UMLGenerator(self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_directory(self):
        """Тест пустой директории"""
        uml_output = self.uml_generator.generate_uml()
        
        # Должен вернуть минимальную валидную структуру
        assert uml_output.startswith("@startuml")
        assert uml_output.endswith("@enduml")
        assert len(uml_output.split('\n')) == 2

    def test_files_without_classes(self):
        """Тест файлов без классов"""
        test_file = Path(self.temp_dir) / "functions_only.py"
        test_file.write_text("""
def function1():
    return "test1"

def function2():
    return "test2"

variable = "test"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем наличие функций
        assert 'class "function1()"' in uml_output
        assert 'class "function2()"' in uml_output
        
        # Проверяем наличие глобальных переменных
        assert 'class "Global Variables"' in uml_output
        assert "+ variable" in uml_output

    def test_files_with_only_global_variables(self):
        """Тест файлов только с глобальными переменными"""
        test_file = Path(self.temp_dir) / "globals_only.py"
        test_file.write_text("""
CONSTANT = "value"
variable = 42
_protected_var = "protected"
__private_var = "private"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем наличие глобальных переменных
        assert 'class "Global Variables"' in uml_output
        assert "+ CONSTANT" in uml_output
        assert "+ variable" in uml_output
        assert "# _protected_var" in uml_output
        assert "- __private_var" in uml_output

    def test_complex_ast_structures(self):
        """Тест сложных AST структур"""
        test_file = Path(self.temp_dir) / "complex.py"
        test_file.write_text("""
# Лямбда-функции
lambda_func = lambda x: x * 2

# Генераторы
def generator_func():
    for i in range(10):
        yield i

# Вложенные классы
class OuterClass:
    class InnerClass:
        def inner_method(self):
            return "inner"
    
    def outer_method(self):
        return "outer"

# Множественное наследование
class Base1:
    def method1(self):
        return "base1"

class Base2:
    def method2(self):
        return "base2"

class MultiInherited(Base1, Base2):
    def multi_method(self):
        return "multi"

# Декораторы классов
def class_decorator(cls):
    return cls

@class_decorator
class DecoratedClass:
    def decorated_method(self):
        return "decorated"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем основные классы
        assert "class OuterClass" in uml_output
        assert "class MultiInherited" in uml_output
        assert "class DecoratedClass" in uml_output
        
        # Проверяем отношения наследования
        assert "Base1 <|-- MultiInherited" in uml_output
        assert "Base2 <|-- MultiInherited" in uml_output

    def test_very_long_names(self):
        """Тест очень длинных имен"""
        long_name = "a" * 1000
        test_file = Path(self.temp_dir) / "long_names.py"
        test_file.write_text(f"""
class {long_name}:
    def __init__(self):
        self.{long_name}_field = "value"
    
    def {long_name}_method(self):
        return "test"

{long_name}_global = "global"
def {long_name}_function():
    return "function"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем, что длинные имена обработаны
        assert f"class {long_name}" in uml_output
        assert f"+ {long_name}_field" in uml_output
        assert f"+ {long_name}_method()" in uml_output
        assert f"+ {long_name}_global" in uml_output
        assert f'class "{long_name}_function()"' in uml_output

    def test_special_characters_in_names(self):
        """Тест специальных символов в именах"""
        test_file = Path(self.temp_dir) / "special_chars.py"
        test_file.write_text("""
class Test_Class_With_Underscores:
    def __init__(self):
        self.field_with_underscores = "value"
    
    def method_with_underscores(self):
        return "test"

class TestClassWithNumbers123:
    def method123(self):
        return "test"

# Глобальные переменные с специальными символами
test_variable_123 = "value"
TEST_CONSTANT_456 = "constant"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем обработку специальных символов
        assert "class Test_Class_With_Underscores" in uml_output
        assert "+ field_with_underscores" in uml_output
        assert "+ method_with_underscores()" in uml_output
        assert "class TestClassWithNumbers123" in uml_output
        assert "+ method123()" in uml_output
        assert "+ test_variable_123" in uml_output
        assert "+ TEST_CONSTANT_456" in uml_output

    def test_paths_with_special_characters(self):
        """Тест путей со специальными символами"""
        # Создаем директорию с специальными символами
        special_dir = Path(self.temp_dir) / "test-dir_with_underscores"
        special_dir.mkdir()
        
        test_file = special_dir / "test-file_with_underscores.py"
        test_file.write_text("""
class TestClass:
    def test_method(self):
        return "test"
""")
        
        # Создаем новый генератор для специальной директории
        uml_generator = UMLGenerator(special_dir)
        uml_output = uml_generator.generate_uml()
        
        # Проверяем обработку путей со специальными символами
        assert "class TestClass" in uml_output
        assert "+ test_method()" in uml_output

    def test_symlinks_and_cyclic_references(self):
        """Тест симлинков и циклических ссылок"""
        # Создаем основной файл
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def main_method(self):
        return "main"
""")
        
        # Создаем симлинк (если поддерживается)
        try:
            symlink_file = Path(self.temp_dir) / "symlink.py"
            symlink_file.symlink_to(main_file)
            
            uml_output = self.uml_generator.generate_uml()
            
            # Проверяем, что симлинк обработан корректно
            assert "class MainClass" in uml_output
        except (OSError, NotImplementedError):
            # Симлинки могут не поддерживаться на некоторых системах
            pass

    def test_very_large_files(self):
        """Тест очень больших файлов"""
        # Создаем файл с большим количеством классов
        large_file = Path(self.temp_dir) / "large.py"
        content = ""
        
        for i in range(100):
            content += f"""
class Class{i}:
    def __init__(self):
        self.field{i} = "value{i}"
    
    def method{i}(self):
        return "method{i}"
"""
        
        large_file.write_text(content)
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем, что все классы обработаны
        for i in range(100):
            assert f"class Class{i}" in uml_output
            assert f"+ field{i}" in uml_output
            assert f"+ method{i}()" in uml_output

    def test_unicode_characters(self):
        """Тест Unicode символов"""
        test_file = Path(self.temp_dir) / "unicode.py"
        test_file.write_text("""
class КлассСРусскимиСимволами:
    def __init__(self):
        self.поле = "значение"
    
    def метод(self):
        return "тест"

class ClassWithUnicode:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"

# Глобальные переменные с Unicode
переменная = "значение"
VARIABLE = "value"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем обработку Unicode символов
        assert "class КлассСРусскимиСимволами" in uml_output
        assert "+ поле" in uml_output
        assert "+ метод()" in uml_output
        assert "class ClassWithUnicode" in uml_output
        assert "+ field" in uml_output
        assert "+ method()" in uml_output
        assert "+ переменная" in uml_output
        assert "+ VARIABLE" in uml_output

    def test_nested_packages(self):
        """Тест вложенных пакетов"""
        # Создаем глубоко вложенную структуру
        deep_dir = Path(self.temp_dir)
        for i in range(5):
            deep_dir = deep_dir / f"level{i}"
            deep_dir.mkdir()
        
        # Создаем файл в самом глубоком уровне
        test_file = deep_dir / "deep.py"
        test_file.write_text("""
class DeepClass:
    def deep_method(self):
        return "deep"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем обработку глубоко вложенных пакетов
        assert "class DeepClass" in uml_output
        assert "+ deep_method()" in uml_output
        assert 'package "level0.level1.level2.level3.level4.deep"' in uml_output

    def test_empty_classes(self):
        """Тест пустых классов"""
        test_file = Path(self.temp_dir) / "empty.py"
        test_file.write_text("""
class EmptyClass:
    pass

class ClassWithOnlyPass:
    def method(self):
        pass

class ClassWithDocstring:
    \"\"\"Docstring only\"\"\"
    pass
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем обработку пустых классов
        assert "class EmptyClass" in uml_output
        assert "class ClassWithOnlyPass" in uml_output
        assert "class ClassWithDocstring" in uml_output
        assert "+ method()" in uml_output

    def test_comments_and_docstrings(self):
        """Тест комментариев и докстрингов"""
        test_file = Path(self.temp_dir) / "comments.py"
        test_file.write_text("""
# Это комментарий
class TestClass:
    \"\"\"Это докстринг класса\"\"\"
    
    def __init__(self):
        # Комментарий в методе
        self.field = "value"
    
    def method(self):
        \"\"\"Это докстринг метода\"\"\"
        return "test"

# Еще один комментарий
def function():
    \"\"\"Докстринг функции\"\"\"
    return "function"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем, что комментарии и докстринги не мешают обработке
        assert "class TestClass" in uml_output
        assert "+ field" in uml_output
        assert "+ method()" in uml_output
        assert 'class "function()"' in uml_output

    def test_imports_and_from_imports(self):
        """Тест импортов"""
        test_file = Path(self.temp_dir) / "imports.py"
        test_file.write_text("""
import os
import sys
from pathlib import Path
from typing import List, Dict
from abc import ABC, abstractmethod

class TestClass:
    def method(self):
        return "test"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем, что импорты не мешают обработке классов
        assert "class TestClass" in uml_output
        assert "+ method()" in uml_output

    def test_try_except_blocks(self):
        """Тест блоков try-except"""
        test_file = Path(self.temp_dir) / "try_except.py"
        test_file.write_text("""
class TestClass:
    def method_with_try(self):
        try:
            return "success"
        except Exception:
            return "error"
    
    def method_with_finally(self):
        try:
            return "try"
        finally:
            return "finally"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем обработку методов с try-except
        assert "class TestClass" in uml_output
        assert "+ method_with_try()" in uml_output
        assert "+ method_with_finally()" in uml_output

    def test_decorators(self):
        """Тест декораторов"""
        test_file = Path(self.temp_dir) / "decorators.py"
        test_file.write_text("""
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class TestClass:
    @my_decorator
    def decorated_method(self):
        return "decorated"
    
    @property
    def property_method(self):
        return "property"
    
    @classmethod
    def class_method(cls):
        return "class"
    
    @staticmethod
    def static_method():
        return "static"
""")
        
        uml_output = self.uml_generator.generate_uml()
        
        # Проверяем обработку декорированных методов
        assert "class TestClass" in uml_output
        assert "+ decorated_method()" in uml_output
        assert "+ property_method()" in uml_output
        assert "+ class_method()" in uml_output
        assert "+ {static} static_method()" in uml_output 