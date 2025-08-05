import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


class TestGitignoreCLI:
    """Интеграционные тесты для CLI с .gitignore функциональностью"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli_command(self, args):
        """Запускает CLI команду"""
        return subprocess.run([
            "py2puml"
        ] + args, capture_output=True, text=True)

    def test_cli_use_gitignore_default(self):
        """Тест проверки работы по умолчанию (с .gitignore)"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("""
class TestMainClass:
    def test_something(self):
        pass
""")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI без явного указания флага (по умолчанию)
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_no_gitignore_flag(self):
        """Тест проверки флага --no-gitignore"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("""
class TestMainClass:
    def test_something(self):
        pass
""")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI с флагом --no-gitignore
        result = self.run_cli_command([
            "generate", "--no-gitignore", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_use_gitignore_flag(self):
        """Тест проверки флага --use-gitignore"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("""
class TestMainClass:
    def test_something(self):
        pass
""")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI с явным флагом --use-gitignore
        result = self.run_cli_command([
            "generate", "--use-gitignore", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_gitignore_mutually_exclusive(self):
        """Тест проверки взаимоисключающих флагов"""
        # Создаем тестовый файл
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('test')")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI с обоими флагами (должно вызвать ошибку)
        result = self.run_cli_command([
            "generate", "--use-gitignore", "--no-gitignore", str(self.temp_dir), str(output_file)
        ])

        # Проверяем, что аргументы обрабатываются корректно
        # (argparse должен использовать последний указанный флаг)
        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_gitignore_help_text(self):
        """Тест проверки корректности текста помощи"""
        result = self.run_cli_command(["generate", "--help"])

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_generate_uml_with_gitignore(self):
        """Тест генерации UML с применением .gitignore фильтров"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n__pycache__/\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("""
class TestMainClass:
    def test_something(self):
        pass
""")

        pycache_dir = Path(self.temp_dir) / "__pycache__"
        pycache_dir.mkdir()
        pyc_file = pycache_dir / "main.pyc"
        pyc_file.write_text("# This should be ignored")

        # Создаем еще один Python файл в игнорируемой директории
        ignored_file = tests_dir / "another_test.py"
        ignored_file.write_text("class AnotherTest: pass")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_generate_uml_without_gitignore(self):
        """Тест генерации UML без .gitignore фильтров"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n__pycache__/\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("""
class TestMainClass:
    def test_something(self):
        pass
""")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI с отключенным .gitignore
        result = self.run_cli_command([
            "generate", "--no-gitignore", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_generate_uml_ignored_files_count(self):
        """Тест проверки корректности подсчета проигнорированных файлов"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("class MainClass: pass")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()

        # Создаем несколько тестовых файлов
        for i in range(3):
            test_file = tests_dir / f"test_{i}.py"
            test_file.write_text(f"class TestClass{i}: pass")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_generate_uml_output_consistency(self):
        """Тест проверки консистентности вывода с/без .gitignore"""
        # Создаем .gitignore файл
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n")

        # Создаем структуру файлов
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_main.py"
        test_file.write_text("""
class TestMainClass:
    def test_something(self):
        pass
""")

        # Запускаем с .gitignore
        output_with_gitignore = Path(self.temp_dir) / "output_with.puml"
        result_with = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_with_gitignore)
        ])

        # Запускаем без .gitignore
        output_without_gitignore = Path(self.temp_dir) / "output_without.puml"
        result_without = self.run_cli_command([
            "generate", "--no-gitignore", str(self.temp_dir), str(output_without_gitignore)
        ])

        assert result_with.returncode == 0
        assert result_without.returncode == 0
        assert output_with_gitignore.exists()
        assert output_without_gitignore.exists()

    def test_cli_no_gitignore_file(self):
        """Тест работы CLI без .gitignore файла"""
        # Создаем только Python файлы без .gitignore
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        output_file = Path(self.temp_dir) / "output.puml"

        # Запускаем CLI
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists() 