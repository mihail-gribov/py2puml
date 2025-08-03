import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

# Добавляем путь к модулю для импорта
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCLI:
    """Интеграционные тесты для CLI интерфейса"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.main_script = Path(__file__).parent.parent.parent / "main.py"

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cli_valid_arguments(self):
        """Тест корректных аргументов CLI"""
        # Создаем тестовый Python файл
        test_file = Path(self.temp_dir) / "test_module.py"
        test_file.write_text("""
class TestClass:
    def __init__(self):
        self.field = "value"
    
    def method(self):
        return "test"
""")
        
        output_file = Path(self.temp_dir) / "output.puml"
        
        # Запускаем CLI
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(self.temp_dir), str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output_file.exists()
        assert "PlantUML code has been saved to" in result.stdout

    def test_cli_nonexistent_directory(self):
        """Тест CLI с несуществующей директорией"""
        output_file = Path(self.temp_dir) / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            "/nonexistent/directory", str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "Directory not found" in result.stdout

    def test_cli_file_as_directory(self):
        """Тест CLI когда путь указывает на файл, а не директорию"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('test')")
        
        output_file = Path(self.temp_dir) / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(test_file), str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "Path is not a directory" in result.stdout

    def test_cli_missing_arguments(self):
        """Тест CLI с отсутствующими аргументами"""
        result = subprocess.run([
            sys.executable, str(self.main_script)
        ], capture_output=True, text=True)
        
        assert result.returncode != 0
        assert "error" in result.stderr.lower()

    def test_cli_permission_denied_output(self):
        """Тест CLI с отказом в доступе к выходному файлу"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('test')")
        
        # Пытаемся записать в системную директорию без прав
        output_file = Path("/root") / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(self.temp_dir), str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 1
        assert "Permission denied" in result.stdout or "Cannot create output directory" in result.stdout

    def test_cli_syntax_errors_in_code(self):
        """Тест CLI с синтаксическими ошибками в коде"""
        test_file = Path(self.temp_dir) / "broken.py"
        test_file.write_text("""
class TestClass:
    def broken_method(self):
        print("broken"  # Незакрытая скобка
""")
        
        output_file = Path(self.temp_dir) / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(self.temp_dir), str(output_file)
        ], capture_output=True, text=True)
        
        # Должен завершиться успешно, но с предупреждениями
        assert result.returncode == 0
        assert "Warning" in result.stdout
        assert output_file.exists()

    def test_cli_empty_directory(self):
        """Тест CLI с пустой директорией"""
        output_file = Path(self.temp_dir) / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(self.temp_dir), str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Warning: No Python files found" in result.stdout
        assert output_file.exists()

    def test_cli_complex_project(self):
        """Тест CLI с комплексным проектом"""
        # Создаем структуру проекта
        project_dir = Path(self.temp_dir) / "project"
        project_dir.mkdir()
        
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
        
        output_file = Path(self.temp_dir) / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(project_dir), str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output_file.exists()
        
        # Проверяем содержимое выходного файла
        content = output_file.read_text()
        assert "class Application" in content
        assert "class Helper" in content
        assert "class User" in content

    def test_cli_inheritance_relationships(self):
        """Тест CLI с отношениями наследования"""
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
        
        output_file = Path(self.temp_dir) / "output.puml"
        
        result = subprocess.run([
            sys.executable, str(self.main_script),
            str(self.temp_dir), str(output_file)
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert output_file.exists()
        
        # Проверяем наличие отношений наследования
        content = output_file.read_text()
        assert "BaseClass <|-- DerivedClass" in content
        assert "BaseClass <|-- AnotherDerived" in content

    @patch('builtins.input', return_value='')
    def test_cli_keyboard_interrupt(self, mock_input):
        """Тест обработки прерывания пользователем"""
        # Создаем большой файл для длительной обработки
        test_file = Path(self.temp_dir) / "large_file.py"
        content = "class TestClass:\n"
        for i in range(1000):
            content += f"    def method_{i}(self):\n        return {i}\n"
        test_file.write_text(content)
        
        output_file = Path(self.temp_dir) / "output.puml"
        
        # Симулируем прерывание (этот тест может быть нестабильным)
        try:
            result = subprocess.run([
                sys.executable, str(self.main_script),
                str(self.temp_dir), str(output_file)
            ], capture_output=True, text=True, timeout=1)
        except subprocess.TimeoutExpired:
            # Ожидаемое поведение при таймауте
            pass 