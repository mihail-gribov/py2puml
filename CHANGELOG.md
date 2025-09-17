# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Custom class formatting system** with background colors for different class types
  - Regular classes: Standard styling with default background
  - Abstract classes: `abstract` keyword with white background (`#FFFFFF`)
  - Dataclasses: `class` keyword with green background (`#90EE90`) - replaces `dataclass` keyword
  - Interfaces: `interface` keyword with white background (`#FFFFFF`)
  - PlantUML syntax: Uses `<< (C,#COLOR) >>` for proper background color rendering
- **Smart decorator handling** for `@dataclass` - decorator excluded from class name (handled by styling)
- **Style configuration system** in `core/parser.py` with `CLASS_STYLE_CONFIG`
- **Enhanced class type detection** with base type mapping
- **Examples directory** with comprehensive test cases for custom formatting
- **Documentation** for custom class formatting feature

### Changed
- **Class formatting logic** updated to use background colors instead of border colors
- **PlantUML syntax** changed from `#COLOR` to `<< (C,#COLOR) >>` for proper background rendering
- **Dataclass display** now uses `class` keyword with green background instead of `dataclass` keyword
- **Abstract class display** now uses `abstract` keyword with white background
- **Interface display** now uses `interface` keyword with white background

### Fixed
- **Double hash symbol issue** in PlantUML color syntax (was `##COLOR`, now `#COLOR`)
- **Background color rendering** in PlantUML diagrams
- **Decorator handling** for dataclasses to prevent duplicate display

### Technical Details
- Modified `core/parser.py`: Added `CLASS_STYLE_CONFIG` and `get_class_style()` method
- Modified `core/generator.py`: Updated `_format_class_info()` for background color syntax
- Modified `py2uml.py`: Updated for compatibility with new formatting system
- Updated `_determine_class_type()` to return base types instead of descriptive names
- Updated `_format_name_with_decorators()` to exclude `@dataclass` decorator

## [Previous Versions]

### Features
- Comprehensive Python code analysis
- PlantUML diagram generation
- File description feature with multiple output formats
- Documentation extraction
- Inheritance support
- Visibility management
- Property access annotations
- Decorator handling
- Error handling and visual error marking
- Type hint support
- Modern CLI architecture
- Standalone single-file script
