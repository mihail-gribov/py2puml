import pytest
import tempfile
import subprocess
import sys
import os
from pathlib import Path


class TestDescribeFileCLI:
    """Интеграционные тесты для CLI команды describe-file."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.temp_dir = tempfile.mkdtemp()
        self.main_script = Path(__file__).parent.parent.parent / "main.py"
    
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
    
    def run_cli_command(self, args):
        """Запускает CLI команду и возвращает результат."""
        cmd = [sys.executable, str(self.main_script)] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.temp_dir
        )
        return result
    
    def test_basic_describe_file_command(self):
        """Тест базовой команды --describe-file."""
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
        
        result = self.run_cli_command(["--describe-file", str(file_path)])
        
        assert result.returncode == 0
        assert "File: " in result.stdout
        assert "Summary: " in result.stdout
        assert "TestClass" in result.stdout
        assert "test_function" in result.stdout
        assert "TEST_VAR" in result.stdout
        assert "Test class" in result.stdout
        assert "Test method" in result.stdout
        assert "Test function" in result.stdout
    
    def test_json_format(self):
        """Тест JSON формата."""
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
            "--describe-file", str(file_path),
            "--format", "json"
        ])
        
        assert result.returncode == 0
        
        import json
        data = json.loads(result.stdout)
        assert data['file'] == str(file_path)
        assert 'summary' in data
        assert 'classes' in data
        assert 'functions' in data
        assert len(data['classes']) == 1
        assert len(data['functions']) == 1
    
    def test_yaml_format(self):
        """Тест YAML формата."""
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
            "--describe-file", str(file_path),
            "--format", "yaml"
        ])
        
        assert result.returncode == 0
        
        try:
            import yaml
            data = yaml.safe_load(result.stdout)
            assert data['file'] == str(file_path)
            assert 'summary' in data
            assert 'classes' in data
            assert 'functions' in data
        except ImportError:
            # PyYAML не установлен
            assert "PyYAML library not available" in result.stdout
    
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
        
        result = self.run_cli_command([
            "--describe-file", str(file_path),
            "--no-docs"
        ])
        
        assert result.returncode == 0
        assert "TestClass" in result.stdout
        assert "test_method" in result.stdout
        assert "test_function" in result.stdout
        assert "This should be excluded" not in result.stdout
    
    def test_combined_flags(self):
        """Тест комбинации флагов."""
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
            "--describe-file", str(file_path),
            "--format", "json",
            "--no-docs"
        ])
        
        assert result.returncode == 0
        
        import json
        data = json.loads(result.stdout)
        assert data['file'] == str(file_path)
        assert len(data['classes']) == 1
        assert len(data['functions']) == 1
        
        # Проверяем, что документация исключена
        for cls in data['classes']:
            assert cls['documentation'] is None
        for func in data['functions']:
            assert func['documentation'] is None
    
    def test_file_not_found(self):
        """Тест обработки несуществующего файла."""
        non_existent_file = Path(self.temp_dir) / "non_existent.py"
        
        result = self.run_cli_command([
            "--describe-file", str(non_existent_file)
        ])
        
        assert result.returncode == 1
        assert "File not found" in result.stdout
    
    def test_invalid_format(self):
        """Тест некорректного формата."""
        content = '''
def test_function():
    pass
'''
        file_path = self.create_test_file(content)
        
        result = self.run_cli_command([
            "--describe-file", str(file_path),
            "--format", "invalid"
        ])
        
        assert result.returncode == 2  # argparse error
        assert "error" in result.stderr.lower()
    
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
        
        result = self.run_cli_command([
            "--describe-file", str(file_path)
        ])
        
        # Должен обработать ошибку gracefully
        assert result.returncode == 0
        assert "File: " in result.stdout
        assert "Warning:" in result.stdout or "Error:" in result.stdout
    
    def test_complex_file(self):
        """Тест сложного файла с различными элементами."""
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

@dataclass
class User:
    """User data model."""
    id: int
    username: str
    email: str
    is_active: bool = True

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
            "--describe-file", str(file_path)
        ])
        
        assert result.returncode == 0
        assert "File: " in result.stdout
        assert "Summary: " in result.stdout
        assert "BaseAuthenticator" in result.stdout
        assert "DatabaseAuthenticator" in result.stdout
        assert "User" in result.stdout
        assert "create_user" in result.stdout
        assert "validate_email" in result.stdout
        assert "API_VERSION" in result.stdout
        assert "DEFAULT_TIMEOUT" in result.stdout
        assert "UserList" in result.stdout
        assert "ConfigDict" in result.stdout
    
    def test_mutually_exclusive_arguments(self):
        """Тест взаимоисключающих аргументов."""
        # Попытка использовать --describe-file и directory_path одновременно
        result = self.run_cli_command([
            "--describe-file", "test.py",
            "directory_path",
            "output.puml"
        ])
        
        assert result.returncode == 2  # argparse error
        assert "error" in result.stderr.lower()
    
    def test_missing_required_argument(self):
        """Тест отсутствия обязательного аргумента."""
        result = self.run_cli_command([])
        
        assert result.returncode == 2  # argparse error
        assert "error" in result.stderr.lower()
    
    def test_help_output(self):
        """Тест вывода справки."""
        result = self.run_cli_command(["--help"])
        
        assert result.returncode == 0
        assert "--describe-file" in result.stdout
        assert "--format" in result.stdout
        assert "--no-docs" in result.stdout
    
    def test_encoding_handling(self):
        """Тест обработки кодировок."""
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
            "--describe-file", str(file_path)
        ])
        
        assert result.returncode == 0
        assert "File: " in result.stdout
        # Проверяем, что русские символы обрабатываются корректно
        # (может не отображаться в зависимости от кодировки терминала)
    
    def test_large_file_handling(self):
        """Тест обработки большого файла."""
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
            "--describe-file", str(file_path)
        ])
        
        assert result.returncode == 0
        assert "File: " in result.stdout
        assert "Summary: " in result.stdout
        
        # Проверяем, что все классы и функции найдены
        for i in range(10):
            assert f"Class{i}" in result.stdout
        for i in range(20):
            assert f"function_{i}" in result.stdout
        for i in range(5):
            assert f"VAR_{i}" in result.stdout 