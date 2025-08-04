import ast
import os
import sys
from pathlib import Path

# Проверяем доступность pathspec
try:
    import pathspec
    PATHSPEC_AVAILABLE = True
except ImportError:
    PATHSPEC_AVAILABLE = False
    print("Warning: pathspec library not available. Using simple .gitignore patterns.", file=sys.stderr)

class UMLGenerator:
    def __init__(self, directory_path, use_gitignore=True):
        self.directory = Path(directory_path)
        self.use_gitignore = use_gitignore
        self.uml = '@startuml\n'
        self.all_class_bases = {}
        self.errors = []  # Список для хранения ошибок
        self.files_with_errors = {}  # Словарь для хранения файлов с ошибками: {file_path: [error_messages]}
        self.gitignore_specs = {}  # {directory_path: GitIgnoreSpec}
        if self.use_gitignore:
            self._load_gitignore_patterns()

    def visibility(self, name):
        """
        Determine the visibility of a member based on its name.
        """
        if name.startswith('__') and name.endswith('__'):
            return '~', 'private'  # Magic
        if name.startswith('__'):
            return '-', 'private'  # Private
        elif name.startswith('_'):
            return '#', 'protected'  # Protected
        else:
            return '+', 'public'  # Public

    def _load_gitignore_patterns(self):
        """
        Load all .gitignore files in the project recursively.
        """
        try:
            # Найти все .gitignore файлы рекурсивно
            gitignore_files = list(self.directory.rglob('.gitignore'))
            
            for gitignore_file in gitignore_files:
                try:
                    gitignore_dir = gitignore_file.parent
                    if PATHSPEC_AVAILABLE:
                        # Используем pathspec для корректной обработки паттернов
                        with open(gitignore_file, 'r', encoding='utf-8') as f:
                            patterns = f.read().splitlines()
                        spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
                        self.gitignore_specs[str(gitignore_dir)] = spec
                    else:
                        # Простая реализация без pathspec
                        patterns = self._load_simple_gitignore_patterns(gitignore_file)
                        self.gitignore_specs[str(gitignore_dir)] = patterns
                except Exception as e:
                    print(f"Warning: Error reading .gitignore file {gitignore_file}: {e}", file=sys.stderr)
                    continue
        except Exception as e:
            print(f"Warning: Error loading .gitignore patterns: {e}", file=sys.stderr)

    def _load_simple_gitignore_patterns(self, gitignore_file):
        """
        Simple implementation for .gitignore patterns without pathspec.
        """
        try:
            patterns = []
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            return patterns
        except Exception as e:
            print(f"Warning: Error reading .gitignore file {gitignore_file}: {e}", file=sys.stderr)
            return []

    def _should_ignore(self, file_path):
        """
        Check if a file should be ignored based on .gitignore patterns.
        """
        if not self.use_gitignore:
            return False
        
        if PATHSPEC_AVAILABLE:
            return self._should_ignore_pathspec(file_path)
        else:
            return self._should_ignore_simple(file_path)

    def _should_ignore_pathspec(self, file_path):
        """
        Check if file should be ignored using pathspec library.
        """
        try:
            relative_path = file_path.relative_to(self.directory)
            
            # Проверяем все .gitignore файлы, которые могут влиять на этот файл
            for gitignore_dir, spec in self.gitignore_specs.items():
                gitignore_path = Path(gitignore_dir)
                if gitignore_path in file_path.parents or gitignore_path == file_path.parent:
                    # Проверяем относительно директории .gitignore файла
                    try:
                        relative_to_gitignore = file_path.relative_to(gitignore_path)
                        if spec.match_file(relative_to_gitignore):
                            return True
                    except ValueError:
                        # Файл не находится в поддиректории .gitignore
                        continue
            return False
        except Exception as e:
            print(f"Warning: Error checking .gitignore for {file_path}: {e}", file=sys.stderr)
            return False

    def _should_ignore_simple(self, file_path):
        """
        Simple implementation for checking .gitignore patterns.
        """
        try:
            relative_path = file_path.relative_to(self.directory)
            
            for gitignore_dir, spec in self.gitignore_specs.items():
                gitignore_path = Path(gitignore_dir)
                if gitignore_path in file_path.parents or gitignore_path == file_path.parent:
                    try:
                        relative_to_gitignore = file_path.relative_to(gitignore_path)
                        relative_str = str(relative_to_gitignore).replace('\\', '/')
                        
                        # Проверяем тип spec - если это PathSpec объект, пропускаем
                        if hasattr(spec, 'match_file'):
                            # Это PathSpec объект, пропускаем для fallback
                            continue
                        
                        # Это список паттернов для fallback
                        for pattern in spec:
                            if self._match_simple_pattern(relative_str, pattern):
                                return True
                    except ValueError:
                        continue
            return False
        except Exception as e:
            print(f"Warning: Error checking .gitignore for {file_path}: {e}", file=sys.stderr)
            return False

    def _match_simple_pattern(self, file_path, pattern):
        """
        Simple pattern matching for .gitignore patterns.
        """
        import fnmatch
        
        # Убираем ведущий слеш если есть
        if pattern.startswith('/'):
            pattern = pattern[1:]
        
        # Обрабатываем паттерны с **
        if '**' in pattern:
            # Простая реализация для **
            pattern = pattern.replace('**', '*')
        
        # Обрабатываем паттерны с ведущим !
        if pattern.startswith('!'):
            return False  # Упрощенная обработка
        
        # Обрабатываем паттерны директорий (заканчивающиеся на /)
        if pattern.endswith('/'):
            # Проверяем, начинается ли путь с этой директории
            return file_path.startswith(pattern)
        
        # Используем fnmatch для базового сопоставления
        return fnmatch.fnmatch(file_path, pattern)

    def parse_python_file(self, file_path):
        """
        Parse a Python file to extract class and function definitions, global variables, and class inheritance.
        """
        try:
            # Проверяем существование файла
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                self.errors.append(error_msg)
                self.files_with_errors[str(file_path)] = [error_msg]
                print(f"Warning: {error_msg}")
                return [], [], [], {}
            
            # Проверяем права на чтение
            if not os.access(file_path, os.R_OK):
                error_msg = f"Permission denied reading file: {file_path}"
                self.errors.append(error_msg)
                self.files_with_errors[str(file_path)] = [error_msg]
                print(f"Warning: {error_msg}")
                return [], [], [], {}
            
            with open(file_path, "r", encoding='utf-8') as file:
                try:
                    content = file.read()
                    node = ast.parse(content, filename=file_path.name)
                except SyntaxError as e:
                    error_msg = f"Syntax error in {file_path}: {e}"
                    self.errors.append(error_msg)
                    self.files_with_errors[str(file_path)] = [error_msg]
                    print(f"Warning: {error_msg}")
                    # Попытка частичного парсинга отдельных блоков
                    return self._parse_file_partially(content, file_path)
                except UnicodeDecodeError as e:
                    error_msg = f"Encoding error in {file_path}: {e}"
                    self.errors.append(error_msg)
                    self.files_with_errors[str(file_path)] = [error_msg]
                    print(f"Warning: {error_msg}")
                    return [], [], [], {}
                
        except Exception as e:
            error_msg = f"Unexpected error reading {file_path}: {e}"
            self.errors.append(error_msg)
            self.files_with_errors[str(file_path)] = [error_msg]
            print(f"Warning: {error_msg}")
            return [], [], [], {}
        
        classes = []
        functions = []
        class_bases = {}
        global_vars = []
        
        try:
            for n in node.body:
                if isinstance(n, ast.ClassDef):
                    try:
                        class_name, fields, attributes, static_methods, methods, abstract_method_count = self.process_class_def(n)
                        total_method_count = len(static_methods) + len(methods)
                        bases = [base.id for base in n.bases if isinstance(base, ast.Name)]
                        class_type = self.determine_class_type(len(fields) > 0, abstract_method_count, total_method_count, bases)
                        class_bases[class_name] = bases
                        classes.append((
                            class_name,
                            sorted(list(set(fields)), key=lambda x: x[1]),
                            sorted(list(set(attributes)), key=lambda x: x[1]),
                            sorted(list(set(static_methods)), key=lambda x: x[1]),
                            sorted(list(set(methods)), key=lambda x: x[1]),
                            class_type,
                            bases
                        ))
                    except Exception as e:
                        error_msg = f"Error processing class in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
                elif isinstance(n, ast.FunctionDef):
                    try:
                        functions.append(self.process_function_def(n))
                    except Exception as e:
                        error_msg = f"Error processing function in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
                elif isinstance(n, ast.AsyncFunctionDef):
                    try:
                        functions.append(self.process_function_def(n))
                    except Exception as e:
                        error_msg = f"Error processing async function in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
                elif isinstance(n, ast.Assign):
                    try:
                        global_vars.extend(self.process_global_vars(n))
                    except Exception as e:
                        error_msg = f"Error processing global variables in {file_path}: {e}"
                        self.errors.append(error_msg)
                        if str(file_path) not in self.files_with_errors:
                            self.files_with_errors[str(file_path)] = []
                        self.files_with_errors[str(file_path)].append(error_msg)
                        print(f"Warning: {error_msg}")
                        continue
                        
        except Exception as e:
            error_msg = f"Error processing AST nodes in {file_path}: {e}"
            self.errors.append(error_msg)
            if str(file_path) not in self.files_with_errors:
                self.files_with_errors[str(file_path)] = []
            self.files_with_errors[str(file_path)].append(error_msg)
            print(f"Warning: {error_msg}")
            return [], [], [], {}
            
        return (
            classes,
            functions,
            sorted(list(set(global_vars)), key=lambda x: x[1]),
            class_bases
        )

    def _parse_file_partially(self, content, file_path):
        """
        Попытка частичного парсинга файла с синтаксическими ошибками.
        Использует регулярные выражения для извлечения отдельных классов.
        """
        import re
        
        classes = []
        functions = []
        global_vars = []
        class_bases = {}
        
        def try_parse_class_block(class_text, class_name):
            """Попытка парсить отдельный класс"""
            try:
                # Парсим как отдельный модуль
                node = ast.parse(class_text)
                for n in node.body:
                    if isinstance(n, ast.ClassDef) and n.name == class_name:
                        class_name, fields, attributes, static_methods, methods, abstract_method_count = self.process_class_def(n)
                        total_method_count = len(static_methods) + len(methods)
                        bases = [base.id for base in n.bases if isinstance(base, ast.Name)]
                        class_type = self.determine_class_type(len(fields) > 0, abstract_method_count, total_method_count, bases)
                        class_bases[class_name] = bases
                        classes.append((
                            class_name,
                            sorted(list(set(fields)), key=lambda x: x[1]),
                            sorted(list(set(attributes)), key=lambda x: x[1]),
                            sorted(list(set(static_methods)), key=lambda x: x[1]),
                            sorted(list(set(methods)), key=lambda x: x[1]),
                            class_type,
                            bases
                        ))
                        return True
            except Exception as e:
                error_msg = f"Error parsing class {class_name} in {file_path}: {e}"
                self.errors.append(error_msg)
                print(f"Warning: {error_msg}")
                return False
            return False
        
        # Используем регулярное выражение для поиска классов
        # Паттерн ищет "class Name:" с учетом отступов и захватывает весь блок
        class_pattern = r'^(\s*)class\s+(\w+).*?(?=^\1(?:class\s|\w|\Z)|\Z)'
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('class '):
                # Извлекаем имя класса
                class_match = re.match(r'\s*class\s+(\w+)', line)
                if class_match:
                    class_name = class_match.group(1)
                    
                    # Найдем блок класса
                    class_lines = [line]
                    base_indent = len(line) - len(line.lstrip())
                    
                    # Собираем все строки, принадлежащие этому классу
                    j = i + 1
                    while j < len(lines):
                        current_line = lines[j]
                        if current_line.strip() == '':
                            class_lines.append(current_line)
                        else:
                            current_indent = len(current_line) - len(current_line.lstrip())
                            # Если отступ больше базового или это пустая строка - принадлежит классу
                            if current_indent > base_indent:
                                class_lines.append(current_line)
                            else:
                                # Если встретили строку с таким же или меньшим отступом - конец класса
                                break
                        j += 1
                    
                    # Проверим, есть ли незакрытые скобки в блоке класса
                    class_text = '\n'.join(class_lines)
                    
                    # Попробуем исправить простые синтаксические ошибки
                    try:
                        # Проверим баланс скобок в каждой строке метода
                        corrected_lines = []
                        for line in class_lines:
                            corrected_line = line
                            # Подсчитаем открытые скобки
                            open_parens = corrected_line.count('(')
                            close_parens = corrected_line.count(')')
                            
                            # Если есть незакрытые скобки в строке с print, try to fix
                            if open_parens > close_parens and ('print(' in corrected_line or 'print (' in corrected_line):
                                # Добавим недостающие закрывающие скобки
                                corrected_line += ')' * (open_parens - close_parens)
                            
                            corrected_lines.append(corrected_line)
                        
                        corrected_text = '\n'.join(corrected_lines)
                        
                        # Пробуем сначала исправленный текст
                        if try_parse_class_block(corrected_text, class_name):
                            continue
                        
                        # Если исправленный не работает, попробуем оригинальный
                        if try_parse_class_block(class_text, class_name):
                            continue
                            
                    except Exception as e:
                        error_msg = f"Failed to parse class {class_name} in {file_path}: {e}"
                        self.errors.append(error_msg)
                        print(f"Warning: {error_msg}")
        
        return (
            classes,
            functions,
            sorted(list(set(global_vars)), key=lambda x: x[1]),
            class_bases
        )

    def _process_ast_node(self, node, classes, functions, global_vars, class_bases, file_path):
        """Обработка отдельного AST узла"""
        try:
            for n in node.body:
                if isinstance(n, ast.ClassDef):
                    try:
                        class_name, fields, attributes, static_methods, methods, abstract_method_count = self.process_class_def(n)
                        total_method_count = len(static_methods) + len(methods)
                        bases = [base.id for base in n.bases if isinstance(base, ast.Name)]
                        class_type = self.determine_class_type(len(fields) > 0, abstract_method_count, total_method_count, bases)
                        class_bases[class_name] = bases
                        classes.append((
                            class_name,
                            sorted(list(set(fields)), key=lambda x: x[1]),
                            sorted(list(set(attributes)), key=lambda x: x[1]),
                            sorted(list(set(static_methods)), key=lambda x: x[1]),
                            sorted(list(set(methods)), key=lambda x: x[1]),
                            class_type,
                            bases
                        ))
                    except Exception as e:
                        error_msg = f"Error processing class in {file_path}: {e}"
                        self.errors.append(error_msg)
                        print(f"Warning: {error_msg}")
                        
                elif isinstance(n, ast.FunctionDef):
                    try:
                        functions.append(self.process_function_def(n))
                    except Exception as e:
                        error_msg = f"Error processing function in {file_path}: {e}"
                        self.errors.append(error_msg)
                        
                elif isinstance(n, ast.Assign):
                    try:
                        global_vars.extend(self.process_global_vars(n))
                    except Exception as e:
                        error_msg = f"Error processing global variables in {file_path}: {e}"
                        self.errors.append(error_msg)
                        print(f"Warning: {error_msg}")
                        
        except Exception as e:
            error_msg = f"Error processing AST nodes in {file_path}: {e}"
            self.errors.append(error_msg)
            print(f"Warning: {error_msg}")

    def extract_fields_from_init(self, init_method):
        """
        Extract fields defined in the __init__ method of a class.
        """
        try:
            fields = []
            for stmt in init_method.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                            try:
                                prefix, _ = self.visibility(target.attr)
                                fields.append((prefix, target.attr))
                            except Exception as e:
                                # Пропускаем проблемные поля
                                continue
                elif isinstance(stmt, ast.AnnAssign):
                    if isinstance(stmt.target, ast.Attribute) and isinstance(stmt.target.value, ast.Name) and stmt.target.value.id == 'self':
                        try:
                            prefix, _ = self.visibility(stmt.target.attr)
                            type_annotation = self.get_type_annotation(stmt.annotation) if stmt.annotation else "Any"
                            fields.append((prefix + ' {static}', f"{stmt.target.attr}: {type_annotation}"))
                        except Exception as e:
                            # Пропускаем проблемные поля
                            continue
            return fields
        except Exception as e:
            # Возвращаем пустой список в случае ошибки
            return []

    def process_class_def(self, node):
        """
        Process a class definition node to extract its components.
        """
        try:
            class_name = node.name
            methods = []
            fields = []
            attributes = []
            abstract_method_count = 0
            static_methods = []
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    try:
                        prefix, method_signature, is_abstract, is_static, is_class = self.process_method_def(body_item)
                        if is_abstract:
                            abstract_method_count += 1
                        if is_static or is_class:
                            static_methods.append((prefix, method_signature))
                        else:
                            methods.append((prefix, method_signature))

                        if body_item.name == '__init__':
                            fields = self.extract_fields_from_init(body_item)
                    except Exception as e:
                        # Пропускаем проблемные методы
                        continue

                elif isinstance(body_item, ast.AsyncFunctionDef):
                    try:
                        prefix, method_signature, is_abstract, is_static, is_class = self.process_method_def(body_item)
                        if is_abstract:
                            abstract_method_count += 1
                        if is_static or is_class:
                            static_methods.append((prefix, method_signature))
                        else:
                            methods.append((prefix, method_signature))
                    except Exception as e:
                        # Пропускаем проблемные методы
                        continue

                elif isinstance(body_item, ast.ClassDef):
                    # Рекурсивно обрабатываем вложенные классы
                    try:
                        # Просто пропускаем вложенные классы для упрощения
                        # В будущем можно добавить их отдельную обработку
                        pass
                    except Exception as e:
                        # Пропускаем проблемные вложенные классы
                        continue

                elif isinstance(body_item, ast.AnnAssign):
                    try:
                        attributes.extend(self.process_attributes(body_item))
                    except Exception as e:
                        # Пропускаем проблемные атрибуты
                        continue
            return class_name, fields, attributes, static_methods, methods, abstract_method_count
        except Exception as e:
            # Возвращаем пустые значения в случае ошибки
            return "UnknownClass", [], [], [], [], 0

    def process_method_def(self, body_item):
        """
        Process a method definition node to extract its signature and properties.
        """
        try:
            prefix, vis_type = self.visibility(body_item.name)
            
            # Обрабатываем обычные аргументы
            args = [arg.arg for arg in body_item.args.args]
            
            # Определяем тип метода
            is_abstract = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'abstractmethod' for dec in body_item.decorator_list)
            is_static = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'staticmethod' for dec in body_item.decorator_list)
            is_class = 'decorator_list' in body_item._fields and any(isinstance(dec, ast.Name) and dec.id == 'classmethod' for dec in body_item.decorator_list)
            
            # Убираем self/cls из сигнатуры для всех методов (упрощение UML)
            if is_class and args and args[0] == 'cls':
                args = args[1:]
            elif not is_static and not is_class and args and args[0] == 'self':
                args = args[1:]
            
            # Не добавляем *args и **kwargs в сигнатуру для упрощения
            # if body_item.args.vararg:
            #     args.append(f"*{body_item.args.vararg.arg}")
            # 
            # if body_item.args.kwarg:
            #     args.append(f"**{body_item.args.kwarg.arg}")
            
            method_signature = f"{body_item.name}({', '.join(args)})"
            if is_abstract:
                prefix = prefix + ' {abstract}'
            elif is_static:
                prefix = prefix + ' {static}'
            return prefix, method_signature, is_abstract, is_static, is_class
        except Exception as e:
            # Возвращаем базовую информацию в случае ошибки
            return '+', f"{body_item.name if hasattr(body_item, 'name') else 'unknown'}()", False, False, False

    def process_attributes(self, body_item):
        """
        Process attributes of a class defined using type annotations.
        """
        try:
            attributes = []
            if isinstance(body_item.target, ast.Name):
                prefix, _ = self.visibility(body_item.target.id)
                type_annotation = self.get_type_annotation(body_item.annotation) if body_item.annotation else "Any"
                attributes.append((prefix + ' {static}', f"{body_item.target.id}: {type_annotation}"))
            return attributes
        except Exception as e:
            # Возвращаем пустой список в случае ошибки
            return []

    def get_type_annotation(self, annotation):
        """
        Extract a string representation of a type annotation from the AST.
        Handles common cases like Name, Subscript, and Attribute.
        """
        try:
            if isinstance(annotation, ast.Name):
                return annotation.id
            elif isinstance(annotation, ast.Subscript):
                if isinstance(annotation.slice, ast.Index):
                    return f"{self.get_type_annotation(annotation.value)}[{self.get_type_annotation(annotation.slice.value)}]"
                elif isinstance(annotation.slice, ast.Tuple):
                    # Для Dict[str, int] AST представляет как Dict[(str, int)]
                    # Убираем лишние скобки
                    inner_types = ', '.join(self.get_type_annotation(el) for el in annotation.slice.elts)
                    return f"{self.get_type_annotation(annotation.value)}[{inner_types}]"
                else:
                    return f"{self.get_type_annotation(annotation.value)}[{self.get_type_annotation(annotation.slice)}]"
            elif isinstance(annotation, ast.Attribute):
                return f"{self.get_type_annotation(annotation.value)}.{annotation.attr}"
            elif isinstance(annotation, ast.Tuple):
                return f"({', '.join(self.get_type_annotation(el) for el in annotation.elts)})"
            elif isinstance(annotation, ast.List):
                return f"[{', '.join(self.get_type_annotation(el) for el in annotation.elts)}]"
            else:
                # Для неподдерживаемых типов возвращаем "Any"
                return "Any"
        except Exception as e:
            # В случае ошибки возвращаем "Any"
            return "Any"

    def process_fields(self, body_item):
        """
        Process fields defined using simple assignments.
        """
        fields = []
        for target in body_item.targets:
            if isinstance(target, ast.Name):
                prefix, _ = self.visibility(target.id)
                fields.append((prefix, target.id))
        return fields

    def process_function_def(self, node):
        """
        Process a function definition node to extract its signature.
        """
        try:
            args = ', '.join(arg.arg for arg in node.args.args)
            return f"{node.name}({args})"
        except Exception as e:
            # Возвращаем базовую информацию в случае ошибки
            return f"{node.name if hasattr(node, 'name') else 'unknown'}()"

    def determine_class_type(self, has_fields, abstract_method_count, total_method_count, bases=None):
        """
        Determine the type of class (interface, abstract class, or class) based on its methods and fields.
        """
        # Если класс наследуется от ABC и есть абстрактные методы
        if bases and 'ABC' in bases and abstract_method_count > 0:
            # Interface: несколько абстрактных методов (2+), все методы абстрактные, нет полей
            if (abstract_method_count == total_method_count and 
                abstract_method_count >= 2 and 
                not has_fields):
                return 'interface'
            # Abstract class: один абстрактный метод ИЛИ есть неабстрактные методы вместе с абстрактными
            else:
                return 'abstract class'
        # Если есть абстрактные методы без наследования от ABC
        elif abstract_method_count > 0:
            return 'abstract class'
        return 'class'

    def format_class_info(self, class_info):
        """
        Format the information of a class for UML representation.
        """
        try:
            class_name, fields, attributes, static_methods, methods, class_type, bases = class_info
            class_str = f"  {class_type} {class_name} {{\n"
            
            # Обрабатываем поля
            for prefix, field in fields:
                try:
                    class_str += f"    {prefix} {field}\n"
                except Exception as e:
                    # Пропускаем проблемные поля
                    continue
                    
            if len(fields) and len(methods):
                class_str += "    ....\n"

            # Обрабатываем методы
            for prefix, method in methods:
                try:
                    class_str += f"    {prefix} {method}\n"
                except Exception as e:
                    # Пропускаем проблемные методы
                    continue

            if (len(fields) or len(methods)) and (len(attributes) or len(static_methods)):
                class_str += "    __Static__\n"

            # Обрабатываем атрибуты
            for prefix, attribute in attributes:
                try:
                    class_str += f"    {prefix} {attribute}\n"
                except Exception as e:
                    # Пропускаем проблемные атрибуты
                    continue

            if len(attributes) and len(static_methods):
                class_str += "    ....\n"

            # Обрабатываем статические методы
            for prefix, method in static_methods:
                try:
                    class_str += f"    {prefix} {method}\n"
                except Exception as e:
                    # Пропускаем проблемные статические методы
                    continue

            class_str += "  }\n"
            return class_str
        except Exception as e:
            # Возвращаем базовую информацию в случае ошибки
            class_name = class_info[0] if len(class_info) > 0 else 'UnknownClass'
            return f"  class {class_name} {{\n  }}\n"

    def add_inheritance_relations(self):
        """
        Add inheritance relationships between classes to the UML.
        """
        for class_name, bases in self.all_class_bases.items():
            for base in bases:
                self.uml += f"{base} <|-- {class_name}\n"

    def generate_uml(self):
        """
        Generate UML for all Python files in the specified directory.
        """
        try:
            # Проверяем существование директории
            if not self.directory.exists():
                error_msg = f"Directory not found: {self.directory}"
                self.errors.append(error_msg)
                print(f"Error: {error_msg}")
                return "@startuml\n@enduml"
            
            # Проверяем права на чтение директории
            if not os.access(self.directory, os.R_OK):
                error_msg = f"Permission denied reading directory: {self.directory}"
                self.errors.append(error_msg)
                print(f"Error: {error_msg}")
                return "@startuml\n@enduml"
            
            pathlist = list(self.directory.rglob('*.py'))
            
            if self.use_gitignore:
                original_count = len(pathlist)
                pathlist = [path for path in pathlist if not self._should_ignore(path)]
                ignored_count = original_count - len(pathlist)
                if ignored_count > 0:
                    print(f"Info: {ignored_count} Python files ignored due to .gitignore patterns")
            
            if not pathlist:
                print(f"Warning: No Python files found in {self.directory}")
                return "@startuml\n@enduml"
                
        except Exception as e:
            error_msg = f"Error scanning directory {self.directory}: {e}"
            self.errors.append(error_msg)
            print(f"Error: {error_msg}")
            return "@startuml\n@enduml"
        
        for path in pathlist:
            try:
                relative_path = path.relative_to(self.directory).with_suffix('')
                package_name = str(relative_path).replace('/', '.').replace('\\', '.')  # Handle paths for both Windows and Unix
                class_infos, function_infos, global_vars, class_bases = self.parse_python_file(path)

                self.all_class_bases.update(class_bases)
                
                # Проверяем, есть ли ошибки в этом файле
                file_has_errors = str(path) in self.files_with_errors
                
                if file_has_errors:
                    # Файл с ошибками - красный цвет и специальная иконка
                    self.uml += f'package "{package_name}" <<Frame>> #FF0000 {{\n'
                    # Добавляем комментарий с описанием ошибок
                    self.uml += f'  note right : Ошибки:\n'
                    for error in self.files_with_errors[str(path)]:
                        self.uml += f'  note right : - {error}\n'
                else:
                    # Обычный файл - стандартный цвет
                    self.uml += f'package "{package_name}" <<Frame>> #F0F0FF {{\n'
                
                if global_vars:
                    self.uml += '  class "Global Variables" << (V,#AAAAFF) >> {\n'
                    for prefix, var in global_vars:
                        self.uml += f"    {prefix} {var}\n"
                    self.uml += '  }\n'
                for function_signature in function_infos:
                    self.uml += f'  class "{function_signature}" << (F,#DDDD00) >> {{\n  }}\n'
                for class_info in class_infos:
                    self.uml += self.format_class_info(class_info)

                self.uml += '}\n'
                
            except Exception as e:
                error_msg = f"Error processing file {path}: {e}"
                self.errors.append(error_msg)
                if str(path) not in self.files_with_errors:
                    self.files_with_errors[str(path)] = []
                self.files_with_errors[str(path)].append(error_msg)
                print(f"Warning: {error_msg}")
                continue
        
        try:
            self.add_inheritance_relations()
        except Exception as e:
            error_msg = f"Error adding inheritance relations: {e}"
            self.errors.append(error_msg)
            print(f"Warning: {error_msg}")
        
        self.uml += '@enduml'
        return self.uml

    def process_global_vars(self, node):
        """
        Process global variables defined in the module.
        """
        try:
            global_vars = []
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        prefix, _ = self.visibility(target.id)
                        global_vars.append((prefix, target.id))
                    except Exception as e:
                        # Пропускаем проблемные переменные
                        continue
            return global_vars
        except Exception as e:
            # Возвращаем пустой список в случае ошибки
            return []

    def _extract_documentation(self, node):
        """
        Extract docstring from an AST node.
        """
        try:
            if hasattr(node, 'body') and node.body:
                # Ищем docstring в начале тела
                first_item = node.body[0]
                if isinstance(first_item, ast.Expr) and isinstance(first_item.value, ast.Constant):
                    docstring = first_item.value.value
                    if isinstance(docstring, str) and docstring.strip():
                        return docstring.strip()
            return None
        except Exception:
            return None

    def _get_file_summary(self, file_path, classes, functions, variables):
        """
        Get file summary statistics.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = len(file.readlines())
        except Exception:
            lines = 0
        
        return {
            'lines': lines,
            'classes': len(classes),
            'functions': len(functions),
            'variables': len(variables)
        }

    def describe_file(self, file_path, format='text', include_docs=True):
        """
        Describe a Python file with classes, functions, and variables.
        """
        # Проверяем формат в начале
        if format not in ['text', 'json', 'yaml']:
            raise ValueError(f"Unsupported format: {format}")
        
        try:
            # Конвертируем в Path объект если передана строка
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # Проверяем существование файла
            if not file_path.exists():
                error_msg = f"File not found: {file_path}"
                self.errors.append(error_msg)
                return f"Error: {error_msg}"
            
            # Парсим файл используя существующий метод
            classes, functions, global_vars, class_bases = self.parse_python_file(file_path)
            
            # Получаем статистику файла
            summary = self._get_file_summary(file_path, classes, functions, global_vars)
            
            # Подготавливаем данные для форматирования
            data = {
                'file': str(file_path),
                'summary': summary,
                'classes': [],
                'functions': [],
                'variables': []
            }
            
            # Обрабатываем классы
            for class_info in classes:
                class_name, fields, attributes, static_methods, methods, class_type, bases = class_info
                
                # Извлекаем документацию класса
                class_doc = None
                if include_docs:
                    # Находим AST узел класса для извлечения документации
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef) and node.name == class_name:
                                class_doc = self._extract_documentation(node)
                                break
                    except Exception:
                        pass
                
                class_data = {
                    'name': class_name,
                    'type': class_type,
                    'bases': bases,
                    'documentation': class_doc,
                    'fields': [],
                    'methods': []
                }
                
                # Обрабатываем поля
                for prefix, field in fields:
                    field_data = {
                        'name': field.split(':')[0].strip() if ':' in field else field,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'type': field.split(':')[1].strip() if ':' in field else None
                    }
                    class_data['fields'].append(field_data)
                
                # Обрабатываем методы
                for prefix, method in methods + static_methods:
                    method_name = method.split('(')[0]
                    method_data = {
                        'name': method_name,
                        'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                        'signature': method,
                        'return_type': None,  # TODO: извлечь из аннотаций
                        'documentation': None
                    }
                    
                    # Извлекаем документацию метода
                    if include_docs:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as file:
                                content = file.read()
                            tree = ast.parse(content)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef) and node.name == class_name:
                                    for body_item in node.body:
                                        if isinstance(body_item, ast.FunctionDef) and body_item.name == method_name:
                                            method_data['documentation'] = self._extract_documentation(body_item)
                                            break
                                        elif isinstance(body_item, ast.AsyncFunctionDef) and body_item.name == method_name:
                                            method_data['documentation'] = self._extract_documentation(body_item)
                                            break
                                    break
                        except Exception:
                            pass
                    
                    class_data['methods'].append(method_data)
                
                data['classes'].append(class_data)
            
            # Обрабатываем функции
            for func_signature in functions:
                func_name = func_signature.split('(')[0]
                func_data = {
                    'name': func_name,
                    'visibility': 'public',  # Функции всегда публичные
                    'signature': func_signature,
                    'return_type': None,  # TODO: извлечь из аннотаций
                    'documentation': None
                }
                
                # Извлекаем документацию функции
                if include_docs:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                                func_data['documentation'] = self._extract_documentation(node)
                                break
                            elif isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
                                func_data['documentation'] = self._extract_documentation(node)
                                break
                    except Exception:
                        pass
                
                data['functions'].append(func_data)
            
            # Обрабатываем переменные
            for prefix, var_name in global_vars:
                var_data = {
                    'name': var_name,
                    'visibility': 'public' if prefix.startswith('+') else 'private' if prefix.startswith('-') else 'protected',
                    'type': None,  # TODO: извлечь из аннотаций
                    'documentation': None
                }
                data['variables'].append(var_data)
            
            # Форматируем результат
            if format == 'text':
                return self._format_describe_text(data)
            elif format == 'json':
                return self._format_describe_json(data)
            elif format == 'yaml':
                return self._format_describe_yaml(data)
                
        except Exception as e:
            error_msg = f"Error describing file {file_path}: {e}"
            self.errors.append(error_msg)
            return f"Error: {error_msg}"

    def _format_describe_text(self, data):
        """
        Format data in text format.
        """
        result = f"File: {data['file']}\n"
        result += f"Summary: {data['summary']['lines']} lines, {data['summary']['classes']} classes, {data['summary']['functions']} functions, {data['summary']['variables']} variables\n\n"
        
        if data['classes']:
            result += "Classes:\n"
            for cls in data['classes']:
                result += f"  {cls['name']} ({cls['type']})\n"
                if cls['bases']:
                    result += f"    Bases: {', '.join(cls['bases'])}\n"
                if cls['documentation']:
                    result += f"    Documentation: {cls['documentation']}\n"
                
                if cls['fields']:
                    result += "    Fields:\n"
                    for field in cls['fields']:
                        visibility = field['visibility']
                        field_type = f": {field['type']}" if field['type'] else ""
                        result += f"      {visibility} {field['name']}{field_type}\n"
                
                if cls['methods']:
                    result += "    Methods:\n"
                    for method in cls['methods']:
                        visibility = method['visibility']
                        result += f"      {visibility} {method['signature']}\n"
                        if method['documentation']:
                            result += f"        Documentation: {method['documentation']}\n"
                result += "\n"
        
        if data['functions']:
            result += "Functions:\n"
            for func in data['functions']:
                result += f"  {func['signature']}\n"
                if func['documentation']:
                    result += f"    Documentation: {func['documentation']}\n"
            result += "\n"
        
        if data['variables']:
            result += "Variables:\n"
            for var in data['variables']:
                visibility = var['visibility']
                var_type = f": {var['type']}" if var['type'] else ""
                result += f"  {visibility} {var['name']}{var_type}\n"
                if var['documentation']:
                    result += f"    Documentation: {var['documentation']}\n"
        
        return result

    def _format_describe_json(self, data):
        """
        Format data in JSON format.
        """
        import json
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_describe_yaml(self, data):
        """
        Format data in YAML format.
        """
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            return "Error: PyYAML library not available for YAML formatting"