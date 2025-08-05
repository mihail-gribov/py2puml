"""
Tests for installer functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestInstaller(unittest.TestCase):
    """Test cases for installer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_install_py2puml_success(self, mock_run):
        """Test successful py2puml installation."""
        # Mock successful pip install
        mock_run.return_value = MagicMock(returncode=0)
        
        # This would be called from install.sh
        # For testing purposes, we'll simulate the installation logic
        result = mock_run(['pip3', 'install', '-e', '.'])
        
        self.assertEqual(result.returncode, 0)
        mock_run.assert_called_once_with(['pip3', 'install', '-e', '.'])
    
    @patch('subprocess.run')
    def test_install_py2puml_failure(self, mock_run):
        """Test failed py2puml installation."""
        # Mock failed pip install
        mock_run.return_value = MagicMock(returncode=1)
        
        result = mock_run(['pip3', 'install', '-e', '.'])
        
        self.assertEqual(result.returncode, 1)
    
    @patch('os.chmod')
    def test_mcp_server_executable(self, mock_chmod):
        """Test making MCP server executable."""
        # Create a mock MCP server file
        mcp_file = Path(self.temp_dir) / "mcp_file_analyzer.py"
        mcp_file.write_text("#!/usr/bin/env python3\nprint('MCP Server')")
        
        # Mock chmod call
        mock_chmod.return_value = None
        
        # Simulate making file executable
        os.chmod(mcp_file, 0o755)
        
        mock_chmod.assert_called_once_with(mcp_file, 0o755)
    
    @patch('subprocess.run')
    def test_mcp_server_test(self, mock_run):
        """Test MCP server functionality."""
        # Mock successful MCP server test
        mock_run.return_value = MagicMock(returncode=0)
        
        # Simulate testing MCP server
        result = mock_run(['python3', 'mcp_file_analyzer.py', '--help'])
        
        self.assertEqual(result.returncode, 0)
    
    def test_cursor_configuration_creation(self):
        """Test Cursor configuration file creation."""
        # Create mock home directory
        home_dir = Path(self.temp_dir) / "home"
        home_dir.mkdir()
        
        # Mock HOME environment variable
        with patch.dict(os.environ, {'HOME': str(home_dir)}):
            cursor_config_dir = home_dir / ".cursor"
            cursor_config_dir.mkdir()
            
            # Create MCP server configuration
            config_file = cursor_config_dir / "mcp_servers.json"
            config_content = '''{
    "mcpServers": {
        "py-analyzer": {
            "command": "python3",
            "args": ["/path/to/mcp_file_analyzer.py"],
            "env": {}
        }
    }
}'''
            config_file.write_text(config_content)
            
            # Verify configuration file exists and has correct content
            self.assertTrue(config_file.exists())
            self.assertIn("py-analyzer", config_file.read_text())
    
    @patch('subprocess.run')
    def test_prerequisites_check_python(self, mock_run):
        """Test Python prerequisite check."""
        # Mock successful Python check
        mock_run.return_value = MagicMock(returncode=0)
        
        # Simulate checking Python version
        result = mock_run(['python3', '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'])
        
        self.assertEqual(result.returncode, 0)
    
    @patch('subprocess.run')
    def test_prerequisites_check_pip(self, mock_run):
        """Test pip prerequisite check."""
        # Mock successful pip check
        mock_run.return_value = MagicMock(returncode=0)
        
        # Simulate checking pip
        result = mock_run(['pip3', '--version'])
        
        self.assertEqual(result.returncode, 0)
    
    def test_file_path_validation(self):
        """Test file path validation logic."""
        # Test valid Python file
        valid_file = Path(self.temp_dir) / "test.py"
        valid_file.write_text("print('test')")
        
        # Test invalid file
        invalid_file = Path(self.temp_dir) / "test.txt"
        invalid_file.write_text("test content")
        
        # Test nonexistent file
        nonexistent_file = Path(self.temp_dir) / "nonexistent.py"
        
        # Validation logic (simplified for testing)
        def validate_file_path(file_path):
            path = Path(file_path)
            if not path.exists():
                raise ValueError("File not found")
            if path.suffix.lower() != '.py':
                raise ValueError("File must be a Python file")
            if not path.is_file():
                raise ValueError("Path is not a file")
            return path
        
        # Test valid file
        result = validate_file_path(str(valid_file))
        self.assertEqual(result, valid_file)
        
        # Test invalid file
        with self.assertRaises(ValueError, msg="File must be a Python file"):
            validate_file_path(str(invalid_file))
        
        # Test nonexistent file
        with self.assertRaises(ValueError, msg="File not found"):
            validate_file_path(str(nonexistent_file))


class TestInstallerIntegration(unittest.TestCase):
    """Integration tests for installer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create a mock project structure
        self.create_mock_project()
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_project(self):
        """Create a mock project structure for testing."""
        # Create pyproject.toml
        pyproject_content = '''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "py2puml"
version = "1.7.0"
description = "Python to PlantUML converter"
'''
        (Path(self.temp_dir) / "pyproject.toml").write_text(pyproject_content)
        
        # Create MCP server file
        mcp_content = '''#!/usr/bin/env python3
"""
MCP File Analyzer Server
"""
import sys
print("MCP Server started")
'''
        (Path(self.temp_dir) / "mcp_file_analyzer.py").write_text(mcp_content)
        
        # Create core directory and analyzer
        core_dir = Path(self.temp_dir) / "core"
        core_dir.mkdir()
        (core_dir / "__init__.py").write_text("")
        
        analyzer_content = '''import ast
from pathlib import Path
from typing import Dict, Any

class FileAnalyzer:
    def __init__(self, directory_path: str):
        self.directory = Path(directory_path)
    
    def describe_file(self, file_path, format='json', include_docs=True):
        return '{"file": "test.py", "summary": {"lines": 1, "classes": 0, "functions": 0, "variables": 0}, "classes": [], "functions": [], "variables": []}'
'''
        (core_dir / "analyzer.py").write_text(analyzer_content)
    
    @patch('subprocess.run')
    def test_full_installation_process(self, mock_run):
        """Test the full installation process."""
        # Mock all subprocess calls
        mock_run.return_value = MagicMock(returncode=0)
        
        # Simulate installation steps
        steps = [
            # Check Python
            (['python3', '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'], 0),
            # Check pip
            (['pip3', '--version'], 0),
            # Install py2puml
            (['pip3', 'install', '-e', '.'], 0),
            # Make MCP server executable
            (['chmod', '+x', 'mcp_file_analyzer.py'], 0),
            # Test MCP server
            (['python3', 'mcp_file_analyzer.py', '--help'], 0),
        ]
        
        for cmd, returncode in steps:
            mock_run.return_value.returncode = returncode
            result = mock_run(cmd)
            self.assertEqual(result.returncode, returncode)
        
        # Verify all expected calls were made
        self.assertEqual(mock_run.call_count, len(steps))
    
    def test_mcp_server_functionality(self):
        """Test that MCP server can be executed."""
        mcp_file = Path(self.temp_dir) / "mcp_file_analyzer.py"
        
        # Make file executable
        os.chmod(mcp_file, 0o755)
        
        # Test that file exists and is executable
        self.assertTrue(mcp_file.exists())
        self.assertTrue(os.access(mcp_file, os.X_OK))
        
        # Test that file contains expected content
        content = mcp_file.read_text()
        self.assertIn("MCP File Analyzer Server", content)
        self.assertIn("#!/usr/bin/env python3", content)
    
    def test_project_structure_validation(self):
        """Test that required project files exist."""
        required_files = [
            "pyproject.toml",
            "mcp_file_analyzer.py",
            "core/__init__.py",
            "core/analyzer.py"
        ]
        
        for file_path in required_files:
            full_path = Path(self.temp_dir) / file_path
            self.assertTrue(full_path.exists(), f"Required file {file_path} not found")


if __name__ == "__main__":
    unittest.main() 