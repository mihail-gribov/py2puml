import argparse
import sys
from pathlib import Path
from uml_generator import UMLGenerator

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Generate UML from Python source code.')
        
        # Создаем группу для взаимоисключающих аргументов
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('directory_path', type=str, nargs='?', help='Path to the directory containing Python source files.')
        group.add_argument('--describe-file', type=str, help='Path to a single Python file to describe.')
        
        parser.add_argument('output_file_path', type=str, nargs='?', help='Path to the output file where UML will be saved.')
        parser.add_argument('--use-gitignore', 
                           action='store_true', 
                           default=True,
                           help='Use .gitignore patterns to exclude files (default: True)')
        parser.add_argument('--no-gitignore', 
                           dest='use_gitignore',
                           action='store_false',
                           help='Do not use .gitignore patterns')
        
        # Новые аргументы для describe-file
        parser.add_argument('--format', 
                           choices=['text', 'json', 'yaml'],
                           default='text',
                           help='Output format for describe-file command (default: text)')
        parser.add_argument('--no-docs',
                           action='store_true',
                           help='Exclude documentation from describe-file output')

        args = parser.parse_args()

        # Обработка команды describe-file
        if args.describe_file:
            file_path = Path(args.describe_file)
            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                sys.exit(1)
            
            if not file_path.is_file():
                print(f"Error: Path is not a file: {file_path}")
                sys.exit(1)
            
            # Создаем UML генератор для одного файла
            try:
                uml_generator = UMLGenerator(file_path.parent, use_gitignore=False)
            except Exception as e:
                print(f"Error: Failed to initialize UML generator: {e}")
                sys.exit(1)
            
            # Описываем файл
            try:
                include_docs = not args.no_docs
                result = uml_generator.describe_file(file_path, format=args.format, include_docs=include_docs)
                print(result)
            except Exception as e:
                print(f"Error: Failed to describe file: {e}")
                sys.exit(1)
            
            # Выводим предупреждения, если есть ошибки
            if uml_generator.errors:
                print(f"\nWarning: {len(uml_generator.errors)} errors occurred during processing:")
                for error in uml_generator.errors:
                    print(f"  - {error}")
            
            sys.exit(0)

        # Обработка основной команды UML генерации
        # Проверяем существование входной директории
        input_dir = Path(args.directory_path)
        if not input_dir.exists():
            print(f"Error: Directory not found: {input_dir}")
            sys.exit(1)
        
        if not input_dir.is_dir():
            print(f"Error: Path is not a directory: {input_dir}")
            sys.exit(1)

        # Проверяем возможность создания выходного файла
        output_file = Path(args.output_file_path)
        output_dir = output_file.parent
        if output_dir.exists() and not output_dir.is_dir():
            print(f"Error: Output directory path is not a directory: {output_dir}")
            sys.exit(1)
        
        # Создаем директорию для выходного файла, если она не существует
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error: Cannot create output directory {output_dir}: {e}")
            sys.exit(1)

        # Создаем UML генератор
        try:
            uml_generator = UMLGenerator(args.directory_path, use_gitignore=args.use_gitignore)
        except Exception as e:
            print(f"Error: Failed to initialize UML generator: {e}")
            sys.exit(1)

        # Генерируем UML
        try:
            uml_output = uml_generator.generate_uml()
        except Exception as e:
            print(f"Error: Failed to generate UML: {e}")
            sys.exit(1)

        # Записываем результат в файл
        try:
            with open(args.output_file_path, 'w', encoding='utf-8') as file:
                file.write(uml_output)
        except PermissionError:
            print(f"Error: Permission denied writing to {args.output_file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to write output file {args.output_file_path}: {e}")
            sys.exit(1)

        print(f"PlantUML code has been saved to {args.output_file_path}")
        
        # Выводим предупреждения, если есть ошибки
        if uml_generator.errors:
            print(f"\nWarning: {len(uml_generator.errors)} errors occurred during processing:")
            for error in uml_generator.errors:
                print(f"  - {error}")
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
