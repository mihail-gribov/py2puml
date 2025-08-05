import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


class TestDescribeFileCLI:
    """Интеграционные тесты для CLI команды describe"""

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

    def create_test_file(self, content):
        """Создает тестовый файл с заданным содержимым"""
        test_file = Path(self.temp_dir) / "test.py"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return test_file

    def test_basic_describe_file_command(self):
        """Тест базовой команды describe"""
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

        result = self.run_cli_command(["describe", str(file_path)])

        assert result.returncode == 0
        assert "TestClass" in result.stdout
        assert "test_method" in result.stdout
        assert "test_function" in result.stdout

    def test_json_format(self):
        """Тест JSON формата"""
        content = '''
class TestClass:
    """Test class."""
    pass

def test_function():
    """Test function."""
    pass
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path), "--format", "json"
        ])

        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert data["file"] == str(file_path)
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "TestClass"

    def test_yaml_format(self):
        """Тест YAML формата"""
        content = '''
class TestClass:
    """Test class."""
    pass

def test_function():
    """Test function."""
    pass
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path), "--format", "yaml"
        ])

        assert result.returncode == 0
        import yaml
        data = yaml.safe_load(result.stdout)
        assert data["file"] == str(file_path)
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "TestClass"

    def test_no_docs_flag(self):
        """Тест флага --no-docs"""
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

        result = self.run_cli_command([
            "describe", str(file_path), "--no-docs"
        ])

        assert result.returncode == 0
        assert "TestClass" in result.stdout
        assert "This should be excluded" not in result.stdout

    def test_combined_flags(self):
        """Тест комбинации флагов"""
        content = '''
class TestClass:
    """This should be excluded."""
    pass

def test_function():
    """This should be excluded."""
    pass
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path), "--format", "json", "--no-docs"
        ])

        assert result.returncode == 0
        import json
        data = json.loads(result.stdout)
        assert data["file"] == str(file_path)
        assert len(data["classes"]) == 1

    def test_file_not_found(self):
        """Тест обработки несуществующего файла"""
        non_existent_file = Path(self.temp_dir) / "non_existent.py"

        result = self.run_cli_command([
            "describe", str(non_existent_file)
        ])

        assert result.returncode == 2  # Click возвращает 2 для ошибок валидации
        assert "File" in result.stderr and "does not exist" in result.stderr

    def test_invalid_format(self):
        """Тест некорректного формата"""
        content = '''
def test_function():
    pass
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path), "--format", "invalid"
        ])

        assert result.returncode == 2
        assert "error" in result.stderr.lower()

    def test_syntax_error_handling(self):
        """Тест обработки синтаксических ошибок"""
        content = '''
class TestClass:
    def test_method(self):
        # Неправильный синтаксис
        if True
            pass
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path)
        ])

        # Должен обработать ошибку gracefully
        assert result.returncode == 0
        assert "File:" in result.stdout

    def test_complex_file(self):
        """Тест сложного файла с различными элементами"""
        content = '''
"""Module for testing complex scenarios."""
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

# Global configuration
API_VERSION = "v1.0"
DEFAULT_TIMEOUT = 30

class BaseAuthenticator(ABC):
    """Abstract base class for authentication."""

    def __init__(self, config: Dict[str, str]):
        """Initialize authenticator."""
        self.config = config
        self._cache = {}

    @abstractmethod
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user credentials."""
        pass

    def _validate_config(self) -> bool:
        """Validate configuration."""
        return "api_key" in self.config

class DatabaseAuthenticator(BaseAuthenticator):
    """Database-based authentication."""

    def __init__(self, db_url: str, **kwargs):
        """Initialize database authenticator."""
        super().__init__(kwargs)
        self.db_url = db_url

    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate against database."""
        return True

class User:
    """User data model."""
    def __init__(self, id: int, username: str, email: str):
        self.id = id
        self.username = username
        self.email = email

def create_user(username: str, email: str) -> User:
    """Create a new user."""
    return User(id=1, username=username, email=email)

async def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[^@]+@[^@]+\.[^@]+$'
    return bool(re.match(pattern, email))

# Type aliases
UserList = List[User]
ConfigDict = Dict[str, str]
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path)
        ])

        assert result.returncode == 0
        assert "BaseAuthenticator" in result.stdout
        assert "DatabaseAuthenticator" in result.stdout
        assert "User" in result.stdout
        assert "create_user" in result.stdout

    def test_mutually_exclusive_arguments(self):
        """Тест взаимоисключающих аргументов"""
        # Попытка использовать describe и generate одновременно
        result = self.run_cli_command([
            "describe", "test.py", "generate", "directory", "output.puml"
        ])

        assert result.returncode == 2
        assert "error" in result.stderr.lower()

    def test_missing_required_argument(self):
        """Тест отсутствия обязательного аргумента"""
        result = self.run_cli_command(["describe"])

        assert result.returncode == 2
        assert "error" in result.stderr.lower()

    def test_help_output(self):
        """Тест вывода справки"""
        result = self.run_cli_command(["describe", "--help"])

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_encoding_handling(self):
        """Тест обработки кодировок"""
        content = '''
# -*- coding: utf-8 -*-
"""Модуль с русскими комментариями."""

class ТестовыйКласс:
    """Класс с русским названием."""

    def тестовый_метод(self):
        """Метод с русским названием."""
        return "тест"
'''
        file_path = self.create_test_file(content)

        result = self.run_cli_command([
            "describe", str(file_path)
        ])

        assert result.returncode == 0
        assert "ТестовыйКласс" in result.stdout

    def test_large_file_handling(self):
        """Тест обработки большого файла"""
        # Создаем большой файл с множеством классов и функций
        content = []
        content.append('"""Large test file."""\n')

        for i in range(10):
            content.append(f'''
class Class{i}:
    """Class {i}."""

    def method_{i}(self):
        """Method {i}."""
        pass
''')

        for i in range(20):
            content.append(f'''
def function_{i}():
    """Function {i}."""
    pass
''')

        for i in range(5):
            content.append(f'VAR_{i} = "{i}"\n')

        file_path = self.create_test_file(''.join(content))

        result = self.run_cli_command([
            "describe", str(file_path)
        ])

        assert result.returncode == 0
        assert "Class0" in result.stdout
        assert "function_0" in result.stdout 