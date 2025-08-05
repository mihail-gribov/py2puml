#!/usr/bin/env python3
"""
py2puml CLI - Command-line interface for Python to PlantUML converter (click version).
"""

import sys
from pathlib import Path

# Add current directory to the import path
sys.path.insert(0, str(Path(__file__).parent))

import click

from core.file_filter import FileFilter
from core.generator import UMLGenerator
from core.analyzer import FileAnalyzer
from utils.error_handling import (
    handle_cli_error, print_warnings, validate_file_path,
    validate_directory_path, validate_output_path, validate_format,
    FileNotFoundError, DirectoryNotFoundError, PermissionError, ValidationError
)

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option('1.0.0', '--version', '-v', message='py2puml %(version)s')
def cli():
    """
    Generate PlantUML diagrams from Python source code.

    Examples:
      py2puml generate src/ output/diagram.puml
      py2puml generate src/ output/diagram.puml --no-gitignore
      py2puml describe src/models.py
      py2puml describe src/models.py --format json
      py2puml describe src/models.py --format yaml --no-docs
    """
    pass

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('output_file', type=click.Path())
@click.option('--no-gitignore', is_flag=True, default=False, help='Do not use .gitignore patterns')
@click.option('--use-gitignore', is_flag=True, default=False, help='Use .gitignore patterns (default)')
def generate(directory, output_file, no_gitignore, use_gitignore):
    """Generate UML diagram from Python source files"""
    try:
        # Validate inputs
        directory_path = validate_directory_path(directory)
        output_path = validate_output_path(output_file)

        # Determine gitignore usage
        use_gitignore_flag = True
        if no_gitignore:
            use_gitignore_flag = False
        elif use_gitignore:
            use_gitignore_flag = True

        # Create file filter
        file_filter = FileFilter(str(directory_path), use_gitignore=use_gitignore_flag)

        # Create UML generator
        generator = UMLGenerator(str(directory_path), file_filter)

        # Generate UML
        uml_output = generator.generate_uml()

        # Write output to file
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(uml_output)
        except PermissionError:
            raise PermissionError(f"Permission denied writing to {output_path}")
        except Exception as e:
            raise Exception(f"Failed to write output file {output_path}: {e}")

        click.echo(f"PlantUML code has been saved to {output_path}")

        # Print warnings if any
        all_warnings = generator.errors + generator.parser.errors
        print_warnings(all_warnings)

    except (FileNotFoundError, DirectoryNotFoundError, PermissionError, ValidationError) as e:
        handle_cli_error(e)
    except Exception as e:
        handle_cli_error(e)

@cli.command()
@click.argument('file', type=click.Path(exists=True, dir_okay=False, file_okay=True))
@click.option('--format', 'format_', type=click.Choice(['text', 'json', 'yaml']), default='text', help='Output format (default: text)')
@click.option('--no-docs', is_flag=True, default=False, help='Exclude documentation from output')
def describe(file, format_, no_docs):
    """Describe a Python file with classes, functions, and variables"""
    try:
        # Validate inputs
        file_path = validate_file_path(file)
        format_name = validate_format(format_)

        # Create analyzer
        analyzer = FileAnalyzer(str(Path(file_path).parent))

        # Describe file
        include_docs = not no_docs
        result = analyzer.describe_file(file_path, format=format_name, include_docs=include_docs)

        # Print result
        click.echo(result)

        # Print warnings if any
        print_warnings(analyzer.parser.errors)

    except (FileNotFoundError, DirectoryNotFoundError, PermissionError, ValidationError) as e:
        handle_cli_error(e)
    except Exception as e:
        handle_cli_error(e)

def main():
    cli()

if __name__ == "__main__":
    main() 