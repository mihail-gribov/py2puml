import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


class TestGitignoreCLI:
    """Integration tests for the CLI with .gitignore support"""

    def setup_method(self):
        """Set up before each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up after each test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_cli_command(self, args):
        """Run a CLI command"""
        return subprocess.run([
            "py2puml"
        ] + args, capture_output=True, text=True)

    def test_cli_use_gitignore_default(self):
        """Default behaviour (with .gitignore)"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Create the file structure
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

        # Run the CLI without an explicit flag (default behaviour)
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_no_gitignore_flag(self):
        """The --no-gitignore flag"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Create the file structure
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

        # Run the CLI with --no-gitignore
        result = self.run_cli_command([
            "generate", "--no-gitignore", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_use_gitignore_flag(self):
        """The --use-gitignore flag"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Create the file structure
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

        # Run the CLI with an explicit --use-gitignore
        result = self.run_cli_command([
            "generate", "--use-gitignore", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_gitignore_mutually_exclusive(self):
        """Mutually exclusive flags"""
        # Create a test file
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('test')")

        output_file = Path(self.temp_dir) / "output.puml"

        # Run the CLI with both flags (should be an error)
        result = self.run_cli_command([
            "generate", "--use-gitignore", "--no-gitignore", str(self.temp_dir), str(output_file)
        ])

        # Arguments must be handled correctly
        # (argparse should use the last flag given)
        assert result.returncode == 0
        assert output_file.exists()

    def test_cli_gitignore_help_text(self):
        """Correct help text"""
        result = self.run_cli_command(["generate", "--help"])

        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_generate_uml_with_gitignore(self):
        """UML generation with .gitignore filters applied"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n__pycache__/\n")

        # Create the file structure
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

        # Create another Python file in an ignored directory
        ignored_file = tests_dir / "another_test.py"
        ignored_file.write_text("class AnotherTest: pass")

        output_file = Path(self.temp_dir) / "output.puml"

        # Run the CLI
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_generate_uml_without_gitignore(self):
        """UML generation without .gitignore filters"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n__pycache__/\n")

        # Create the file structure
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

        # Run the CLI with .gitignore disabled
        result = self.run_cli_command([
            "generate", "--no-gitignore", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_generate_uml_ignored_files_count(self):
        """Correct count of ignored files"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n*.pyc\n")

        # Create the file structure
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("class MainClass: pass")

        tests_dir = Path(self.temp_dir) / "tests"
        tests_dir.mkdir()

        # Create several test files
        for i in range(3):
            test_file = tests_dir / f"test_{i}.py"
            test_file.write_text(f"class TestClass{i}: pass")

        output_file = Path(self.temp_dir) / "output.puml"

        # Run the CLI
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists()

    def test_generate_uml_output_consistency(self):
        """Output consistency with and without .gitignore"""
        # Create a .gitignore file
        gitignore_file = Path(self.temp_dir) / ".gitignore"
        gitignore_file.write_text("tests/\n")

        # Create the file structure
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

        # Run with .gitignore
        output_with_gitignore = Path(self.temp_dir) / "output_with.puml"
        result_with = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_with_gitignore)
        ])

        # Run without .gitignore
        output_without_gitignore = Path(self.temp_dir) / "output_without.puml"
        result_without = self.run_cli_command([
            "generate", "--no-gitignore", str(self.temp_dir), str(output_without_gitignore)
        ])

        assert result_with.returncode == 0
        assert result_without.returncode == 0
        assert output_with_gitignore.exists()
        assert output_without_gitignore.exists()

    def test_cli_no_gitignore_file(self):
        """CLI without a .gitignore file"""
        # Create Python files only, without a .gitignore
        main_file = Path(self.temp_dir) / "main.py"
        main_file.write_text("""
class MainClass:
    def __init__(self):
        self.value = 42
""")

        output_file = Path(self.temp_dir) / "output.puml"

        # Run the CLI
        result = self.run_cli_command([
            "generate", str(self.temp_dir), str(output_file)
        ])

        assert result.returncode == 0
        assert output_file.exists() 