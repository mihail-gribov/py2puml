import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from py2puml.core.file_filter import FileFilter


class TestGitignoreFunctionality:
    """Tests for .gitignore functionality"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_filter = FileFilter(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_gitignore_patterns_success(self):
        """Successful loading of .gitignore patterns"""
        gitignore_content = """
*.pyc
__pycache__/
*.log
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Patterns must be loaded
        assert len(file_filter.gitignore_specs) > 0

    def test_load_gitignore_patterns_empty_file(self):
        """Loading an empty .gitignore file"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # The file must be processed without errors
        assert len(file_filter.gitignore_specs) > 0

    def test_load_gitignore_patterns_with_comments(self):
        """Loading a .gitignore with comments"""
        gitignore_content = """
# ignore the Python cache
*.pyc
__pycache__/

# ignore logs
*.log
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Patterns must be loaded
        assert len(file_filter.gitignore_specs) > 0

    def test_load_gitignore_patterns_multiple_files(self):
        """Loading multiple .gitignore files"""
        # Create the root .gitignore
        root_gitignore = Path(self.temp_dir) / ".gitignore"
        with open(root_gitignore, 'w') as f:
            f.write("*.pyc\n")

        # Create a subdirectory with its own .gitignore
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        sub_gitignore = sub_dir / ".gitignore"
        with open(sub_gitignore, 'w') as f:
            f.write("*.tmp\n")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Both files must be loaded
        assert len(file_filter.gitignore_specs) >= 2

    def test_load_gitignore_patterns_nonexistent(self):
        """Loading a missing .gitignore file"""
        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # No errors when .gitignore is absent
        assert isinstance(file_filter.gitignore_specs, dict)

    def test_should_ignore_with_pathspec(self):
        """Ignore matching with pathspec"""
        gitignore_content = """
*.pyc
__pycache__/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # A file that must be ignored
        ignored_file = Path(self.temp_dir) / "test.pyc"
        assert file_filter.should_ignore(ignored_file)
        
        # A file that must not be ignored
        normal_file = Path(self.temp_dir) / "test.py"
        assert not file_filter.should_ignore(normal_file)

    def test_should_ignore_without_pathspec(self):
        """Ignore matching without pathspec"""
        # Simulate pathspec being unavailable
        with patch('py2puml.core.file_filter.PATHSPEC_AVAILABLE', False):
            gitignore_content = """
*.pyc
__pycache__/
"""
            gitignore_path = Path(self.temp_dir) / ".gitignore"
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)

            file_filter = FileFilter(self.temp_dir, use_gitignore=True)
            
            # A file that must be ignored
            ignored_file = Path(self.temp_dir) / "test.pyc"
            assert file_filter.should_ignore(ignored_file)
            
            # A file that must not be ignored
            normal_file = Path(self.temp_dir) / "test.py"
            assert not file_filter.should_ignore(normal_file)

    def test_should_ignore_pattern_matching(self):
        """Pattern matching"""
        gitignore_content = """
*.pyc
test_*.py
dir/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Check assorted patterns
        assert file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")
        assert file_filter.should_ignore(Path(self.temp_dir) / "test_file.py")
        assert not file_filter.should_ignore(Path(self.temp_dir) / "normal.py")

    def test_should_ignore_relative_paths(self):
        """Ignoring relative paths"""
        gitignore_content = """
subdir/
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Create a subdirectory
        subdir = Path(self.temp_dir) / "subdir"
        subdir.mkdir()
        
        # A file in the subdirectory must be ignored
        ignored_file = subdir / "test.py"
        assert file_filter.should_ignore(ignored_file)

    def test_should_ignore_nested_patterns(self):
        """Nested patterns"""
        # Create the root .gitignore
        root_gitignore = Path(self.temp_dir) / ".gitignore"
        with open(root_gitignore, 'w') as f:
            f.write("*.pyc\n")

        # Create a subdirectory with its own .gitignore
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        sub_gitignore = sub_dir / ".gitignore"
        with open(sub_gitignore, 'w') as f:
            f.write("*.tmp\n")

        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        
        # Patterns from both files must apply
        assert file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")
        assert file_filter.should_ignore(sub_dir / "test.tmp")

    def test_gitignore_file_permission_error(self):
        """Permission error on a .gitignore file"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("*.pyc\n")
        
        # Drop read permissions
        os.chmod(gitignore_path, 0o000)
        
        try:
            file_filter = FileFilter(self.temp_dir, use_gitignore=True)
            # Should be processed without errors
            assert isinstance(file_filter.gitignore_specs, dict)
        finally:
            # Restore permissions
            os.chmod(gitignore_path, 0o644)

    def test_gitignore_file_encoding_error(self):
        """Encoding error in a .gitignore file"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # invalid encoding
        
        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        # Should be processed without errors
        assert isinstance(file_filter.gitignore_specs, dict)

    def test_pathspec_import_error(self):
        """pathspec import error"""
        with patch('py2puml.core.file_filter.PATHSPEC_AVAILABLE', False):
            gitignore_content = """
*.pyc
"""
            gitignore_path = Path(self.temp_dir) / ".gitignore"
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)

            file_filter = FileFilter(self.temp_dir, use_gitignore=True)
            
            # Should work through the fallback path
            assert file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")

    def test_gitignore_file_corrupted(self):
        """Corrupted .gitignore file"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("invalid pattern [\n")  # invalid pattern
        
        file_filter = FileFilter(self.temp_dir, use_gitignore=True)
        # Should be processed without errors
        assert isinstance(file_filter.gitignore_specs, dict)

    def test_gitignore_disabled(self):
        """Disabled .gitignore"""
        gitignore_content = """
*.pyc
"""
        gitignore_path = Path(self.temp_dir) / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        file_filter = FileFilter(self.temp_dir, use_gitignore=False)
        
        # With .gitignore disabled nothing must be ignored
        assert not file_filter.should_ignore(Path(self.temp_dir) / "test.pyc")
        assert not file_filter.should_ignore(Path(self.temp_dir) / "test.py") 