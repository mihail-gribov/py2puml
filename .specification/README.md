# PlantUML Specifications

This directory contains specifications and documentation for PlantUML syntax and features.

## Files

- `plantuml_notes_syntax.md` - Complete specification for PlantUML notes syntax
- `plantuml_notes_examples_simple.puml` - Working examples of notes syntax
- `plantuml_notes_examples_simple.png` - Generated diagram from examples

## Usage

These specifications are created to avoid re-investigating PlantUML syntax issues in the future. When working with PlantUML, refer to these files for correct syntax patterns.

## Key Findings

### Notes Syntax
- Notes MUST be attached to specific elements using `note [position] of "element_name"`
- Notes cannot exist standalone inside packages
- Element names must match exactly (case-sensitive)
- Use `end note` for standard notes, `end rnote` for rectangular notes, `end hnote` for hexagonal notes

### Common Mistakes
- Using `note right :` without element attachment
- Incorrect closing tags (`endrnote` instead of `end rnote`)
- Notes inside packages without proper element binding

## Last Updated
September 17, 2024
