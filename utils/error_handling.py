"""
Error handling utilities for py2puml CLI.
"""

import sys
from pathlib import Path
from typing import Optional


class CLIError(Exception):
    """Base exception for CLI errors."""
    pass


class ValidationError(CLIError):
    """Exception raised for validation errors."""
    pass


class FileNotFoundError(CLIError):
    """Exception raised when file is not found."""
    pass


class DirectoryNotFoundError(CLIError):
    """Exception raised when directory is not found."""
    pass


class PermissionError(CLIError):
    """Exception raised for permission errors."""
    pass


def validate_file_path(file_path: str) -> Path:
    """
    Validate file path and return Path object.
    
    Args:
        file_path: Path to validate
        
    Returns:
        Path object
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If path is not a file
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
    
    return path


def validate_directory_path(directory_path: str) -> Path:
    """
    Validate directory path and return Path object.
    
    Args:
        directory_path: Path to validate
        
    Returns:
        Path object
        
    Raises:
        DirectoryNotFoundError: If directory doesn't exist
        ValidationError: If path is not a directory
    """
    path = Path(directory_path)
    
    if not path.exists():
        raise DirectoryNotFoundError(f"Directory not found: {directory_path}")
    
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {directory_path}")
    
    return path


def validate_output_path(output_path: str) -> Path:
    """
    Validate output path and create parent directories if needed.
    
    Args:
        output_path: Path to validate
        
    Returns:
        Path object
        
    Raises:
        PermissionError: If cannot create output directory
    """
    path = Path(output_path)
    output_dir = path.parent
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise PermissionError(f"Cannot create output directory {output_dir}: {e}")
    
    return path


def validate_format(format_name: str) -> str:
    """
    Validate output format.
    
    Args:
        format_name: Format name to validate
        
    Returns:
        Validated format name
        
    Raises:
        ValidationError: If format is not supported
    """
    supported_formats = ['text', 'json', 'yaml']
    
    if format_name not in supported_formats:
        raise ValidationError(f"Unsupported format: {format_name}. Supported formats: {', '.join(supported_formats)}")
    
    return format_name


def handle_cli_error(error: Exception, exit_code: int = 1) -> None:
    """
    Handle CLI error and exit with appropriate code.
    
    Args:
        error: Exception to handle
        exit_code: Exit code to use
    """
    print(f"Error: {error}", file=sys.stderr)
    sys.exit(exit_code)


def print_warnings(warnings: list) -> None:
    """
    Print warnings if any.
    
    Args:
        warnings: List of warning messages
    """
    if warnings:
        print(f"\nWarning: {len(warnings)} warnings occurred during processing:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr) 