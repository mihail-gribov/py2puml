# py2uml.py - Краткая инструкция

**py2uml.py** - это автономный скрипт для генерации UML диаграмм из Python кода в формате PlantUML.

## Основные команды:

### 1. Генерация UML диаграммы:
```bash
python py2uml.py generate <директория> [выходной_файл] [--no-gitignore] [--use-gitignore]
```
*По умолчанию .gitignore используется автоматически*
*Если выходной файл не указан, создается index.puml в анализируемой директории*

### 2. Анализ файла:
```bash
python py2uml.py describe <файл> [--format text|json|yaml] [--no-docs]
```

## Примеры использования:

```bash
# Создать UML диаграмму из папки src/ (сохранится в src/index.puml)
python py2uml.py generate src/

# Создать UML диаграмму с указанным именем файла
python py2uml.py generate src/ output.puml

# Игнорировать .gitignore
python py2uml.py generate src/ output.puml --no-gitignore

# Проанализировать файл в текстовом формате
python py2uml.py describe src/models.py

# Анализ в JSON формате
python py2uml.py describe src/models.py --format json

# Анализ без документации
python py2uml.py describe src/models.py --no-docs
```

## Возможности:
- Генерация полных UML диаграмм из Python кода
- Анализ файлов с выводом в разных форматах (text, JSON, YAML)
- Поддержка .gitignore для фильтрации файлов
- Обработка ошибок и частичный парсинг
- Автономность - не требует установки зависимостей

## Выходные файлы:
- **generate**: создает .puml файл с PlantUML кодом
- **describe**: выводит структурированную информацию о файле

## Опции:
- `--no-gitignore` - игнорировать .gitignore файлы
- `--use-gitignore` - явно использовать .gitignore файлы (по умолчанию включено)
- `--format` - формат вывода для describe (text, json, yaml)
- `--no-docs` - не включать документацию в анализ
