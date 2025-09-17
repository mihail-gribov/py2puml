# Примеры кастомизированного форматирования классов

Эта директория содержит примеры различных типов классов для демонстрации новой системы форматирования в py2puml.

## Файлы с примерами

### 1. `sample_classes.py`
Базовые примеры различных типов классов:
- **RegularClass** - обычный класс (стандартный цвет)
- **AbstractShape** - абстрактный класс (белый цвет)
- **User** - датакласс (зеленый цвет)
- **Point** - замороженный датакласс (зеленый цвет)
- **DatabaseConnection** - интерфейс (белый цвет)
- **Circle** - реализация абстрактного класса
- **Calculator** - обычный класс с методами
- **Square** - еще одна реализация абстрактного класса
- **Product** - датакласс с методами
- **NotificationService** - интерфейс

### 2. `advanced_examples.py`
Продвинутые примеры с более сложной структурой:
- **Status** - перечисление (enum)
- **AbstractRepository** - абстрактный класс с множественными абстрактными методами
- **Order** - сложный датакласс с полями по умолчанию
- **EntityWithTimestamps** - класс с множественным наследованием
- **Validator** - интерфейс
- **InMemoryRepository** - конкретная реализация абстрактного класса
- **Customer** - датакласс с вложенными структурами
- **AbstractPaymentProcessor** - абстрактный класс с конкретными методами
- **Logger** - обычный класс с декораторами методов
- **ConfigProvider** - интерфейс

### 3. `edge_cases.py`
Граничные случаи и сложные сценарии:
- **DataClassWithMethods** - датакласс с дополнительными методами
- **ImplicitDataClass** - класс без методов, но с полями
- **EmptyInterface** - пустой интерфейс
- **PureAbstractClass** - чисто абстрактный класс
- **ComplexDataClass** - сложный датакласс с пост-инициализацией
- **ComplexClass** - сложный обычный класс с различными типами методов
- **AbstractWithConcrete** - абстрактный класс с конкретными методами
- **ConcreteImplementation** - конкретная реализация
- **DerivedDataClass** - наследование датаклассов
- **MultipleInheritanceClass** - множественное наследование

## Как использовать

1. Сгенерировать UML диаграмму для всех примеров:
   ```bash
   python py2uml.py generate examples_custom_formatting output_examples.puml
   ```

2. Сгенерировать диаграмму для конкретного файла:
   ```bash
   python py2uml.py generate examples_custom_formatting/sample_classes.py output_sample.puml
   ```

3. Использовать новый API:
   ```python
   from core.generator import UMLGenerator
   from core.file_filter import FileFilter
   
   file_filter = FileFilter("examples_custom_formatting")
   generator = UMLGenerator("examples_custom_formatting", file_filter)
   uml_output = generator.generate_uml()
   ```

## Ожидаемые результаты форматирования

### Типы классов и их стилизация:

1. **Обычный класс**: `class "ClassName" {` (стандартный цвет)
2. **Абстрактный класс**: `abstract "ClassName" #FFFFFF {` (белый цвет)
3. **Датакласс**: `class "ClassName" #90EE90 {` (зеленый цвет)
4. **Интерфейс**: `interface "ClassName" #FFFFFF {` (белый цвет)

### Примеры PlantUML вывода:

```plantuml
class "RegularClass" {
  + name
  + value
  ....
  ~ __init__(name, value)
  + get_name()
  + get_value()
  + set_value(new_value)
}

abstract "AbstractShape" #FFFFFF {
  + color
  ....
  ~ __init__(color)
  + {abstract} area()
  + {abstract} perimeter()
  + get_color()
}

class "User" #90EE90 {
  + get_display_name()
  + is_adult()
  __Static__
  + age: int
  + email: str
  + is_active: bool
  + name: str
}

interface "DatabaseConnection" #FFFFFF {
}
```

## Особенности реализации

- Датаклассы больше не отображаются с ключевым словом `dataclass`
- Вместо этого используется `class` с зеленым цветом фона
- Абстрактные классы используют `abstract` с белым цветом
- Интерфейсы используют `interface` с белым цветом
- Обычные классы остаются без изменений (стандартный цвет)
- Декоратор `@dataclass` не добавляется к названию класса
