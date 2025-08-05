import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from py2puml.core.file_filter import FileFilter


class TestGitignoreFunctionality:
    """Тесты для функциональности .gitignore"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)

    def teardown_method(self):
        """Очистка после каждого теста"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_gitignore_patterns_success(self):
        """Тест успешной загрузки паттернов .gitignore"""
        gitignore_content = """
*.pyc
__pycache__/
*.log
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что паттерны загружены
        assert len(file_filter.gitignore_specs) > 0

    def test_load_gitignore_patterns_empty_file(self):
        """Тест загрузки пустого .gitignore файла"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что файл обработан без ошибок
        assert len(file_filter.gitignore_specs) > 0

    def test_load_gitignore_patterns_with_comments(self):
        """Тест загрузки .gitignore с комментариями"""
        gitignore_content = """
# Игнорировать Python кэш
*.pyc
__pycache__/

# Игнорировать логи
*.log
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что паттерны загружены
        assert len(file_filter.gitignore_specs) > 0

    def test_load_gitignore_patterns_multiple_files(self):
        """Тест загрузки множественных .gitignore файлов"""
        # Создаем корневой .gitignore
        root_gitignore = Path(self.temp_dir) / ".gitignore"
        with open(root_gitignore, 'w') as f:
            f.write("*.pyc\n")

        # Создаем поддиректорию с .gitignore
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        sub_gitignore = sub_dir / ".gitignore"
        with open(sub_gitignore, 'w') as f:
            f.write("*.tmp\n")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что оба файла загружены
        assert len(file_filter.gitignore_specs) >= 2

    def test_load_gitignore_patterns_nonexistent(self):
        """Тест загрузки несуществующего .gitignore файла"""
        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что нет ошибок при отсутствии .gitignore
        assert isinstance(file_filter.gitignore_specs, dict)

    def test_should_ignore_with_pathspec(self):
        """Тест проверки игнорирования с pathspec"""
        gitignore_content = """
*.pyc
__pycache__/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Файл, который должен быть проигнорирован
        ignored_file = Path(self.temp_dir) / "test.pyc"
        assert file_filter.should_ignore(ignored_file)
        
        # Файл, который не должен быть проигнорирован
        normal_file = Path(self.temp_dir) / "test.py"
        assert not file_filter.should_ignore(normal_file)

    def test_should_ignore_without_pathspec(self):
        """Тест проверки игнорирования без pathspec"""
        # Мокаем отсутствие pathspec
        with patch('py2puml.core.file_filter.PATHSPEC_AVAILABLE', False):
            gitignore_content = """
*.pyc
__pycache__/
"""
            gitignore_path = Path(self.temp_dir) / ".gitignore"
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)

            file_filter = FileFilter(self.temp_dir, use_gitignore=True)
            
            # Файл, который должен быть проигнорирован
            ignored_file = Path(self.temp_dir) / "test.pyc"
            assert file_filter.should_ignore(ignored_file)
            
            # Файл, который не должен быть проигнорирован
            normal_file = Path(self.temp_dir) / "test.py"
            assert not file_filter.should_ignore(normal_file)

    def test_should_ignore_pattern_matching(self):
        """Тест сопоставления паттернов"""
        gitignore_content = """
*.pyc
test_*.py
dir/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем различные паттерны
        assert file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")
        assert file_filter.should_ignore(Path(self.temp_dir) / "test_file.py")
        assert not file_filter.should_ignore(Path(self.temp_dir) / "normal.py")

    def test_should_ignore_relative_paths(self):
        """Тест игнорирования относительных путей"""
        gitignore_content = """
subdir/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Создаем поддиректорию
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        # Файл в поддиректории должен быть проигнорирован
        ignored_file = subdir / "test.py"
        assert file_filter.should_ignore(ignored_file)

    def test_should_ignore_nested_patterns(self):
        """Тест вложенных паттернов"""
        # Создаем корневой .gitignore
        root_gitignore = Path(self.temp_dir) / ".gitignore"
        with open(root_gitignore, 'w') as f:
            f.write("*.pyc\n")

        # Создаем поддиректорию с .gitignore
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        sub_gitignore = sub_dir / ".gitignore"
        with open(sub_gitignore, 'w') as f:
            f.write("*.tmp\n")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Проверяем, что паттерны из обоих файлов работают
        assert file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")
        assert file_filter.should_ignore(sub_dir / "test.tmp")

    def test_gitignore_file_permission_error(self):
        """Тест ошибки доступа к .gitignore файлу"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")
        
        # Убираем права на чтение
        os.chmod(gitignore_path, 0o000)
        
        try:
            file_filter = FileFilter(self.temp_dir, use_gitignore=True)
            # Должно обработаться без ошибок
            assert isinstance(file_filter.gitignore_specs, dict)
        finally:
            # Восстанавливаем права
            os.chmod(gitignore_path, 0o644)

    def test_gitignore_file_encoding_error(self):
        """Тест ошибки кодировки .gitignore файла"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Неправильная кодировка
        
        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        # Должно обработаться без ошибок
        assert isinstance(file_filter.gitignore_specs, dict)

    def test_pathspec_import_error(self):
        """Тест ошибки импорта pathspec"""
        with patch('py2puml.core.file_filter.PATHSPEC_AVAILABLE', False):
            gitignore_content = """
*.pyc
"""
            gitignore_path = Path(self.temp_dir) / ".gitignore"
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)

            file_filter = FileFilter(self.temp_dir, use_gitignore=True)
            
            # Должно работать с fallback
            assert file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")

    def test_gitignore_file_corrupted(self):
        """Тест поврежденного .gitignore файла"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("invalid pattern [\n")  # Неправильный паттерн
        
        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        # Должно обработаться без ошибок
        assert isinstance(file_filter.gitignore_specs, dict)

    def test_gitignore_disabled(self):
        """Тест отключенного .gitignore"""
        gitignore_content = """
*.pyc
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=False)
        
        # При отключенном .gitignore файлы не должны игнорироваться
        assert not file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")
        assert not file_filter.should_ignore(Path(self.temp_dir) / "test.py") 