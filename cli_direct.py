#!/usr/bin/env python3
"""
py2puml CLI - Direct execution version.
"""

import argparse
import sys
from pathlib import Path

# Add src to the import path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from py2puml.core.file_filter import FileFilter
from py2puml.core.generator import UMLGenerator
from py2puml.core.analyzer import FileAnalyzer
from py2puml.utils.error_handling import (
    handle_cli_error, print_warnings, validate_file_path, 
    validate_directory_path, validate_output_path, validate_format,
    FileNotFoundError, DirectoryNotFoundError, PermissionError, ValidationError
)


def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Generate PlantUML diagrams from Python source code.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_direct.py generate src/ output/diagram.puml
  python cli_direct.py generate src/ output/diagram.puml --no-gitignore
  python cli_direct.py describe src/models.py
  python cli_direct.py describe src/models.py --format json
  python cli_direct.py describe src/models.py --format yaml --no-docs
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate UML diagram from Python source files'
    )
    generate_parser.add_argument(
        'directory',
        help='Path to the directory containing Python source files'
    )
    generate_parser.add_argument(
        'output_file',
        help='Path to the output file where UML will be saved'
    )
    generate_parser.add_argument(
        '--no-gitignore',
        action='store_true',
        help='Do not use .gitignore patterns'
    )
    generate_parser.add_argument(
        '--use-gitignore',
        action='store_true',
        help='Use .gitignore patterns (default)'
    )
    
    # Describe command
    describe_parser = subparsers.add_parser(
        'describe',
        help='Describe a Python file with classes, functions, and variables'
    )
    describe_parser.add_argument(
        'file',
        help='Path to the Python file to describe'
    )
    describe_parser.add_argument(
        '--format',
        choices=['text', 'json', 'yaml'],
        default='text',
        help='Output format (default: text)'
    )
    describe_parser.add_argument(
        '--no-docs',
        action='store_true',
        help='Exclude documentation from output'
    )
    
    return parser


def handle_generate_command(args: argparse.Namespace) -> int:
    """
    Handle the generate command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
    try:
        # Validate inputs
        directory_path = validate_directory_path(args.directory)
        output_path = validate_output_path(args.output_file)
        
        # Determine gitignore usage
        use_gitignore = True
        if args.no_gitignore:
            use_gitignore = False
        elif args.use_gitignore:
            use_gitignore = True
        
        # Create file filter
        file_filter = FileFilter(str(directory_path), use_gitignore=use_gitignore)
        
        # Create UML generator
        generator = UMLGenerator(str(directory_path), file_filter)
        
        # Generate UML
        uml_output = generator.generate_uml()
        
        # Write output to file
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(uml_output)
        except PermissionError as e:
            raise PermissionError(f"Permission denied writing to {output_path}")
        except Exception as e:
            raise Exception(f"Failed to write output file {output_path}: {e}")
        
        print(f"PlantUML code has been saved to {output_path}")
        
        # Print warnings if any
        all_warnings = generator.errors + generator.parser.errors
        print_warnings(all_warnings)
        
        return 0
        
    except (FileNotFoundError, DirectoryNotFoundError, PermissionError, ValidationError) as e:
        handle_cli_error(e)
    except Exception as e:
        handle_cli_error(e)


def handle_describe_command(args: argparse.Namespace) -> int:
    """
    Handle the describe command.
    
    Args:
        args: Parsed command arguments
        
    Returns:
        Exit code
    """
    try:
        # Validate inputs
        file_path = validate_file_path(args.file)
        format_name = validate_format(args.format)
        
        # Create analyzer
        analyzer = FileAnalyzer(str(file_path.parent))
        
        # Describe file
        include_docs = not args.no_docs
        result = analyzer.describe_file(file_path, format=format_name, include_docs=include_docs)
        
        # Print result
        print(result)
        
        # Print warnings if any
        print_warnings(analyzer.parser.errors)
        
        return 0
        
    except (FileNotFoundError, DirectoryNotFoundError, PermissionError, ValidationError) as e:
        handle_cli_error(e)
    except Exception as e:
        handle_cli_error(e)


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code
    """
    try:
        parser = create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 1
        
        if args.command == 'generate':
            return handle_generate_command(args)
        elif args.command == 'describe':
            return handle_describe_command(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 1
    except Exception as e:
        handle_cli_error(e)


if __name__ == "__main__":
    sys.exit(main()) 