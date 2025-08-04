import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import ast

# Добавляем путь к модулю для импорта
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from uml_generator import UMLGenerator


class TestGitignoreFunctionality:
    """Тесты для .gitignore функциональности"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.uml_generator = UMLGenerator(self.temp_dir, use_gitignore=True)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_gitignore_patterns_success(self):
        """Тест успешной загрузки .gitignore файла с корректными паттернами"""
        gitignore_content = """
# Python
__pycache__/
*.pyc
*.pyo

# Tests
tests/
*_test.py

# Virtual environments
venv/
.venv/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        # Создаем новый генератор для загрузки паттернов
        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что паттерны загружены
        assert str(self.temp_dir) in generator.gitignore_specs

    def test_load_gitignore_patterns_empty_file(self):
        """Тест обработки пустого .gitignore файла"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("")

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что пустой файл обработан корректно
        assert str(self.temp_dir) in generator.gitignore_specs

    def test_load_gitignore_patterns_with_comments(self):
        """Тест корректной обработки комментариев в .gitignore"""
        gitignore_content = """
# This is a comment
__pycache__/
# Another comment
*.pyc
# Final comment
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что паттерны загружены (комментарии игнорируются)
        assert str(self.temp_dir) in generator.gitignore_specs

    def test_load_gitignore_patterns_multiple_files(self):
        """Тест загрузки нескольких .gitignore файлов в разных директориях"""
        # Создаем структуру директорий
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        # Корневой .gitignore
        root_gitignore = Path(self.temp_dir) / ".gitignore"
        with open(root_gitignore, 'w') as f:
            f.write("__pycache__/\n*.pyc\n")
        
        # Поддиректория .gitignore
        sub_gitignore = subdir / ".gitignore"
        with open(sub_gitignore, 'w') as f:
            f.write("tests/\n*_test.py\n")

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что оба .gitignore файла загружены
        assert str(self.temp_dir) in generator.gitignore_specs
        assert str(subdir) in generator.gitignore_specs

    def test_load_gitignore_patterns_nonexistent(self):
        """Тест обработки отсутствующего .gitignore файла (тихо пропускаем)"""
        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что нет ошибок при отсутствии .gitignore
        assert len(generator.gitignore_specs) == 0

    def test_should_ignore_with_pathspec(self):
        """Тест проверки игнорирования файлов с использованием pathspec"""
        gitignore_content = "tests/\n*.pyc\n"
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Создаем тестовые файлы
        test_file = Path(self.temp_dir) / "tests" / "test_file.py"
        test_file.parent.mkdir()
        test_file.touch()
        
        pyc_file = Path(self.temp_dir) / "main.pyc"
        pyc_file.touch()
        
        normal_file = Path(self.temp_dir) / "main.py"
        normal_file.touch()
        
        # Проверяем игнорирование
        assert generator._should_ignore(test_file) == True
        assert generator._should_ignore(pyc_file) == True
        assert generator._should_ignore(normal_file) == False

    def test_should_ignore_without_pathspec(self):
        """Тест проверки игнорирования файлов без pathspec (fallback)"""
        # Создаем .gitignore файл
        gitignore_content = "tests/\n*.pyc\n"
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        # Создаем генератор и вручную загружаем паттерны для fallback
        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Очищаем gitignore_specs и добавляем паттерны вручную для fallback
        generator.gitignore_specs = {}
        generator.gitignore_specs[str(self.temp_dir)] = ["tests/", "*.pyc"]
        
        # Создаем тестовые файлы
        test_file = Path(self.temp_dir) / "tests" / "test_file.py"
        test_file.parent.mkdir()
        test_file.touch()
        
        pyc_file = Path(self.temp_dir) / "main.pyc"
        pyc_file.touch()
        
        normal_file = Path(self.temp_dir) / "main.py"
        normal_file.touch()
        
        # Проверяем игнорирование через fallback
        assert generator._should_ignore_simple(test_file) == True
        assert generator._should_ignore_simple(pyc_file) == True
        assert generator._should_ignore_simple(normal_file) == False

    def test_should_ignore_pattern_matching(self):
        """Тест тестирования различных паттернов"""
        gitignore_content = """
__pycache__/
*.pyc
tests/
*_test.py
venv/
.venv/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Создаем различные файлы
        files_to_test = [
            (Path(self.temp_dir) / "__pycache__" / "file.pyc", True),
            (Path(self.temp_dir) / "main.pyc", True),
            (Path(self.temp_dir) / "tests" / "test.py", True),
            (Path(self.temp_dir) / "my_test.py", True),
            (Path(self.temp_dir) / "venv" / "file.py", True),
            (Path(self.temp_dir) / ".venv" / "file.py", True),
            (Path(self.temp_dir) / "main.py", False),
            (Path(self.temp_dir) / "src" / "module.py", False),
        ]
        
        for file_path, should_be_ignored in files_to_test:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            assert generator._should_ignore(file_path) == should_be_ignored, f"Failed for {file_path}"

    def test_should_ignore_relative_paths(self):
        """Тест проверки корректной работы с относительными путями"""
        gitignore_content = "tests/\n"
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Создаем файл в поддиректории
        test_file = Path(self.temp_dir) / "tests" / "test.py"
        test_file.parent.mkdir()
        test_file.touch()
        
        # Проверяем, что относительный путь обрабатывается корректно
        assert generator._should_ignore(test_file) == True

    def test_should_ignore_nested_patterns(self):
        """Тест тестирования вложенных паттернов и директорий"""
        # Создаем структуру директорий
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        # Корневой .gitignore
        root_gitignore = Path(self.temp_dir) / ".gitignore"
        with open(root_gitignore, 'w') as f:
            f.write("*.pyc\n")
        
        # Поддиректория .gitignore
        sub_gitignore = subdir / ".gitignore"
        with open(sub_gitignore, 'w') as f:
            f.write("tests/\n")

        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Создаем файлы
        root_pyc = Path(self.temp_dir) / "main.pyc"
        root_pyc.touch()
        
        sub_test = subdir / "tests" / "test.py"
        sub_test.parent.mkdir()
        sub_test.touch()
        
        sub_normal = subdir / "normal.py"
        sub_normal.touch()
        
        # Проверяем игнорирование
        assert generator._should_ignore(root_pyc) == True
        assert generator._should_ignore(sub_test) == True
        assert generator._should_ignore(sub_normal) == False

    def test_gitignore_file_permission_error(self):
        """Тест обработки ошибок доступа к .gitignore файлу"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("tests/\n")
        
        # Делаем файл недоступным для чтения
        os.chmod(gitignore_path, 0o000)
        
        try:
            generator = UMLGenerator(self.temp_dir, use_gitignore=True)
            # Проверяем, что ошибка обработана корректно
            assert len(generator.gitignore_specs) == 0
        finally:
            # Восстанавливаем права
            os.chmod(gitignore_path, 0o644)

    def test_gitignore_file_encoding_error(self):
        """Тест обработки ошибок кодировки в .gitignore файле"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        # Создаем файл с некорректной кодировкой
        with open(gitignore_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Некорректная кодировка
        
        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        # Проверяем, что ошибка обработана корректно
        assert len(generator.gitignore_specs) == 0

    def test_pathspec_import_error(self):
        """Тест корректной работы при отсутствии библиотеки pathspec"""
        # Создаем .gitignore файл
        gitignore_content = "tests/\n*.pyc\n"
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        # Создаем генератор и вручную загружаем паттерны для fallback
        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        
        # Очищаем gitignore_specs и добавляем паттерны вручную для fallback
        generator.gitignore_specs = {}
        generator.gitignore_specs[str(self.temp_dir)] = ["tests/", "*.pyc"]
        
        # Проверяем, что fallback работает
        test_file = Path(self.temp_dir) / "tests" / "test.py"
        test_file.parent.mkdir()
        test_file.touch()
        
        assert generator._should_ignore_simple(test_file) == True

    def test_gitignore_file_corrupted(self):
        """Тест обработки поврежденных .gitignore файлов"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        # Создаем поврежденный файл
        with open(gitignore_path, 'w') as f:
            f.write("tests/\n")
            f.write("broken pattern [\n")  # Некорректный паттерн
        
        generator = UMLGenerator(self.temp_dir, use_gitignore=True)
        # Проверяем, что ошибка обработана корректно
        assert str(self.temp_dir) in generator.gitignore_specs

    def test_gitignore_disabled(self):
        """Тест работы при отключенном .gitignore"""
        gitignore_content = "tests/\n*.pyc\n"
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        generator = UMLGenerator(self.temp_dir, use_gitignore=False)
        
        # Создаем файл, который должен игнорироваться
        test_file = Path(self.temp_dir) / "tests" / "test.py"
        test_file.parent.mkdir()
        test_file.touch()
        
        # Проверяем, что файл НЕ игнорируется при отключенном .gitignore
        assert generator._should_ignore(test_file) == False 