# Custom class formatting examples

This directory holds sample classes of every kind supported by the py2puml
formatting system.

## Example files

### 1. `sample_classes.py`
Basic examples of the different class kinds:
- **RegularClass** - regular class (default colour)
- **AbstractShape** - abstract class (white background)
- **User** - dataclass (green background)
- **Point** - frozen dataclass (green background)
- **DatabaseConnection** - interface (white background)
- **Circle** - implementation of an abstract class
- **Calculator** - regular class with methods
- **Square** - another implementation of an abstract class
- **Product** - dataclass with methods
- **NotificationService** - interface

### 2. `advanced_examples.py`
Advanced examples with a richer structure:
- **Status** - enum
- **AbstractRepository** - abstract class with several abstract methods
- **Order** - complex dataclass with default field values
- **EntityWithTimestamps** - class with multiple inheritance
- **Validator** - interface
- **InMemoryRepository** - concrete implementation of an abstract class
- **Customer** - dataclass with nested structures
- **AbstractPaymentProcessor** - abstract class with concrete methods
- **Logger** - regular class with decorated methods
- **ConfigProvider** - interface

### 3. `edge_cases.py`
Edge cases and tricky scenarios:
- **DataClassWithMethods** - dataclass carrying extra methods
- **ImplicitDataClass** - class without methods but with fields
- **EmptyInterface** - empty interface
- **PureAbstractClass** - purely abstract class
- **ComplexDataClass** - complex dataclass with post-initialisation
- **ComplexClass** - complex regular class with assorted method kinds
- **AbstractWithConcrete** - abstract class with concrete methods
- **ConcreteImplementation** - concrete implementation
- **DerivedDataClass** - dataclass inheritance
- **MultipleInheritanceClass** - multiple inheritance

## How to use

1. Generate a UML diagram for every example:
   ```bash
   python py2uml.py generate examples_custom_formatting output_examples.puml
   ```

2. Generate a diagram for a single file:
   ```bash
   python py2uml.py generate examples_custom_formatting/sample_classes.py output_sample.puml
   ```

3. Use the API directly:
   ```python
   from core.generator import UMLGenerator
   from core.file_filter import FileFilter

   file_filter = FileFilter("examples_custom_formatting")
   generator = UMLGenerator("examples_custom_formatting", file_filter)
   uml_output = generator.generate_uml()
   ```

## Expected formatting

### Class kinds and their styling

1. **Regular class**: `class "ClassName" {` (default colour)
2. **Abstract class**: `abstract "ClassName" #FFFFFF {` (white background)
3. **Dataclass**: `class "ClassName" #90EE90 {` (green background)
4. **Interface**: `interface "ClassName" #FFFFFF {` (white background)

### Sample PlantUML output

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

## Implementation notes

- Dataclasses are no longer rendered with the `dataclass` keyword
- They use `class` with a green background instead
- Abstract classes use `abstract` with a white background
- Interfaces use `interface` with a white background
- Regular classes are unchanged (default colour)
- The `@dataclass` decorator is not appended to the class name
