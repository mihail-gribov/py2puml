import argparse
import sys
from pathlib import Path
from uml_generator import UMLGenerator

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='Generate UML from Python source code.')
        parser.add_argument('directory_path', type=str, help='Path to the directory containing Python source files.')
        parser.add_argument('output_file_path', type=str, help='Path to the output file where UML will be saved.')

        args = parser.parse_args()

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
            uml_generator = UMLGenerator(args.directory_path)
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
