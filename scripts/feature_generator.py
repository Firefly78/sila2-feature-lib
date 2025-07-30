#!/usr/bin/env python3
"""
Script to generate feature_ul and sila_types from labwaresite.sila.xml

This script parses the SiLA XML feature definition and generates:
1. A feature implementation file (feature_ul)
2. Updates to sila_types.py with the data types and errors defined in the XML
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re
import argparse


def snake_to_pascal(snake_str: str) -> str:
    """Convert snake_case to PascalCase"""
    components = snake_str.split('_')
    return ''.join(word.capitalize() for word in components)


def pascal_to_snake(pascal_str: str) -> str:
    """Convert PascalCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', pascal_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def camel_to_snake(camel_str: str) -> str:
    """Convert camelCase to snake_case"""
    # First handle the case where we have consecutive capitals
    s1 = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', camel_str)
    # Then handle normal camelCase
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


def format_docstring(description: str, indent: int = 4, preserve_formatting: bool = False) -> str:
    """Format description as a proper docstring with proper indentation"""
    if not description:
        return ""

    # If preserve_formatting is True, return the description as-is with just indentation
    if preserve_formatting:
        indent_str = " " * indent
        return f"{indent_str}{description}"

    # Clean up the description
    description = description.strip()
    description = re.sub(r'\s+', ' ', description)  # Normalize whitespace

    # Split into lines of reasonable length
    words = description.split()
    lines = []
    current_line = ""
    max_length = 100 - indent  # Account for indentation

    for word in words:
        if len(current_line + " " + word) <= max_length:
            current_line = current_line + " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Format with proper indentation
    indent_str = " " * indent
    return "\n".join(f"{indent_str}{line}" for line in lines)


class SiLAXMLParser:
    def __init__(self, xml_file: Path):
        self.xml_file = xml_file
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.ns = {'sila': 'http://www.sila-standard.org'}

        # Parsed data
        self.feature_info = {}
        self.commands = []
        self.properties = []
        self.data_types = []
        self.execution_errors = []

        self._parse()

    def _parse(self):
        """Parse the XML file and extract all relevant information"""
        self._parse_feature_info()
        self._parse_commands()
        self._parse_properties()
        self._parse_data_types()
        self._parse_execution_errors()

    def _parse_feature_info(self):
        """Parse basic feature information"""
        self.feature_info = {
            'identifier': self.root.find('sila:Identifier', self.ns).text,
            'display_name': self.root.find('sila:DisplayName', self.ns).text,
            'description': self.root.find('sila:Description', self.ns).text.strip()
        }

    def _parse_commands(self):
        """Parse all commands from the XML"""
        for command in self.root.findall('sila:Command', self.ns):
            cmd_info = {
                'identifier': command.find('sila:Identifier', self.ns).text,
                'display_name': command.find('sila:DisplayName', self.ns).text,
                'description': command.find('sila:Description', self.ns).text.strip(),
                'observable': command.find('sila:Observable', self.ns).text == 'Yes',
                'parameters': [],
                'errors': []
            }

            # Parse parameters
            for param in command.findall('sila:Parameter', self.ns):
                param_info = self._parse_parameter(param)
                cmd_info['parameters'].append(param_info)

            # Parse errors
            for error in command.findall('sila:DefinedExecutionErrors', self.ns):
                cmd_info['errors'].append({'identifier': error.find('sila:Identifier', self.ns).text})

            self.commands.append(cmd_info)

    def _parse_properties(self):
        """Parse all properties from the XML"""
        for prop in self.root.findall('sila:Property', self.ns):
            prop_info = {
                'identifier': prop.find('sila:Identifier', self.ns).text,
                'display_name': prop.find('sila:DisplayName', self.ns).text,
                'description': prop.find('sila:Description', self.ns).text.strip(),
                'observable': prop.find('sila:Observable', self.ns).text == 'Yes',
                'data_type': self._parse_data_type(prop.find('sila:DataType', self.ns))
            }
            self.properties.append(prop_info)

    def _parse_parameter(self, param_elem):
        """Parse a single parameter"""
        return {
            'identifier': param_elem.find('sila:Identifier', self.ns).text,
            'display_name': param_elem.find('sila:DisplayName', self.ns).text,
            'description': param_elem.find('sila:Description', self.ns).text.strip(),
            'data_type': self._parse_data_type(param_elem.find('sila:DataType', self.ns))
        }

    def _parse_data_type(self, data_type_elem):
        """Parse data type information"""
        if data_type_elem is None:
            return {'type': 'unknown'}

        # Check for basic types
        basic = data_type_elem.find('sila:Basic', self.ns)
        if basic is not None:
            return {'type': 'basic', 'name': basic.text}

        # Check for custom data type identifiers
        identifier = data_type_elem.find('sila:DataTypeIdentifier', self.ns)
        if identifier is not None:
            return {'type': 'custom', 'name': identifier.text}

        # Check for lists
        list_elem = data_type_elem.find('sila:List', self.ns)
        if list_elem is not None:
            inner_type = self._parse_data_type(list_elem.find('sila:DataType', self.ns))
            return {'type': 'list', 'inner_type': inner_type}

        # Check for constrained types
        constrained = data_type_elem.find('sila:Constrained', self.ns)
        if constrained is not None:
            base_type = self._parse_data_type(constrained.find('sila:DataType', self.ns))
            constraints = {}
            constraints_elem = constrained.find('sila:Constraints', self.ns)
            if constraints_elem is not None:
                min_incl = constraints_elem.find('sila:MinimalInclusive', self.ns)
                if min_incl is not None:
                    constraints['min_inclusive'] = int(min_incl.text)
            return {'type': 'constrained', 'base_type': base_type, 'constraints': constraints}

        return {'type': 'unknown'}

    def _parse_data_types(self):
        """Parse all custom data type definitions"""
        for data_type in self.root.findall('sila:DataTypeDefinition', self.ns):
            type_info = {
                'identifier': data_type.find('sila:Identifier', self.ns).text,
                'display_name': data_type.find('sila:DisplayName', self.ns).text,
                'description': data_type.find('sila:Description', self.ns).text.strip(),
                'definition': self._parse_structure(data_type.find('.//sila:Structure', self.ns))
            }
            self.data_types.append(type_info)

    def _parse_structure(self, structure_elem):
        """Parse a structure data type definition"""
        if structure_elem is None:
            return []

        elements = []
        for element in structure_elem.findall('sila:Element', self.ns):
            elem_info = {
                'identifier': element.find('sila:Identifier', self.ns).text,
                'display_name': element.find('sila:DisplayName', self.ns).text,
                'description': element.find('sila:Description', self.ns).text.strip(),
                'data_type': self._parse_data_type(element.find('sila:DataType', self.ns))
            }
            elements.append(elem_info)
        return elements

    def _parse_execution_errors(self):
        """Parse all defined execution errors"""
        for error in self.root.findall('sila:DefinedExecutionError', self.ns):
            error_info = {
                'identifier': error.find('sila:Identifier', self.ns).text,
                'display_name': error.find('sila:DisplayName', self.ns).text,
                'description': error.find('sila:Description', self.ns).text.strip()
            }
            self.execution_errors.append(error_info)


class FeatureGenerator:
    def __init__(self, parser: SiLAXMLParser):
        self.parser = parser

    def generate_feature_ul(self) -> str:
        """Generate the feature_ul Python code"""
        code_lines = []

        # Imports
        code_lines.extend([
            "import logging",
            "from abc import ABCMeta, abstractmethod",
            "from typing import Annotated"
            "",
            "from unitelabs.cdk import sila",
            "",
            "from .types.sila_types import " + ", ".join(self._get_import_types()),
            "",
            "logger = logging.getLogger(__name__)",
            "",
            ""
        ])

        # Class definition
        class_name = self.parser.feature_info['identifier']
        code_lines.append(f"class {class_name}(sila.Feature, metaclass=ABCMeta):")

        # Class docstring
        description = self.parser.feature_info['description']
        code_lines.append('    """')
        code_lines.extend(format_docstring(description, 4, preserve_formatting=True).split('\n'))
        code_lines.append('    """')
        code_lines.append("")

        # Generate commands
        for command in self.parser.commands:
            code_lines.extend(self._generate_command(command))
            code_lines.append("")

        # Generate properties
        for prop in self.parser.properties:
            code_lines.extend(self._generate_property(prop))
            code_lines.append("")

        return "\n".join(code_lines)

    def _get_import_types(self) -> list[str]:
        """Get list of types that need to be imported"""
        types = set()

        # Add custom data types
        for data_type in self.parser.data_types:
            types.add(data_type['identifier'])

        # Add execution errors
        for error in self.parser.execution_errors:
            types.add(error['identifier'])

        return sorted(list(types))

    def _generate_command(self, command: dict) -> list[str]:
        """Generate code for a single command"""
        lines = []

        # Decorator
        method_name = command['identifier']
        display_name = command['display_name']
        errors_list = f"[{', '.join([e['identifier'] for e in command['errors']])}]" if command['errors'] else "[]"

        lines.append("    @abstractmethod")
        if command['observable']:
            lines.append(f'    @sila.ObservableCommand(name="{display_name}", errors={errors_list})')
        else:
            lines.append(f'    @sila.UnobservableCommand(name="{display_name}", errors={errors_list})')

        # Method signature
        params = ["self"]
        for param in command['parameters']:
            param_type = self._get_python_type(param['data_type'])
            param_name = param['identifier']
            params.append(f"{param_name}: {param_type}")

        if command['observable']:
            params.append("*")
            params.append("status: sila.Status")

        params_str = ",\n        ".join(params) if params else ""
        if params_str:
            params_str = "\n        " + params_str + ",\n    "

        return_type = "None" if command['observable'] else "None"  # Could be expanded based on return types

        lines.append(f"    async def {method_name}({params_str}) -> {return_type}:")

        # Docstring
        lines.append('        """')
        lines.extend(format_docstring(command['description'], 8).split('\n'))
        lines.append("")

        # Parameter documentation
        for param in command['parameters']:
            param_desc = param['description']
            lines.extend(format_docstring(f".. parameter:: {param_desc}", 8).split('\n'))

        lines.append('        """')
        lines.append("        raise NotImplementedError")

        return lines

    def _generate_property(self, prop: dict) -> list[str]:
        """Generate code for a single property"""
        lines = []

        # Decorator
        method_name = prop['identifier']
        display_name = prop['display_name']

        lines.append("    @abstractmethod")
        if prop['observable']:
            lines.append(f'    @sila.ObservableProperty(name="{display_name}")')
        else:
            lines.append(f'    @sila.UnobservableProperty(name="{display_name}")')

        # Method signature
        return_type = self._get_python_type(prop['data_type'])
        lines.append(f"    async def {method_name}(self) -> {return_type}:")

        # Docstring
        lines.append('        """')
        lines.extend(format_docstring(prop['description'], 8).split('\n'))
        lines.append('        """')
        lines.append("        raise NotImplementedError")

        return lines

    def _get_python_type(self, data_type_def: dict) -> str:
        """Convert data type definition to Python type annotation"""
        if data_type_def['type'] == 'basic':
            type_map = {
                'String': 'str',
                'Integer': 'int',
                'Real': 'float',
                'Boolean': 'bool'
            }
            return type_map.get(data_type_def['name'], 'str')

        elif data_type_def['type'] == 'custom':
            return data_type_def['name']

        elif data_type_def['type'] == 'list':
            inner_type = self._get_python_type(data_type_def['inner_type'])
            return f"list[{inner_type}]"

        elif data_type_def['type'] == 'constrained':
            base_type = self._get_python_type(data_type_def['base_type'])
            constraints = data_type_def.get('constraints', {})
            if 'min_inclusive' in constraints:
                return f"Annotated[{base_type}, sila.constraints.MinimalInclusive({constraints['min_inclusive']})]"
            return base_type

        raise ValueError(f"Unknown data type: {data_type_def}")


class SiLATypesGenerator:
    def __init__(self, parser: SiLAXMLParser):
        self.parser = parser

    def generate_sila_types(self) -> str:
        """Generate the sila_types.py content"""
        code_lines = [
            "import dataclasses",
            "from typing import Annotated"
            "",
            "from unitelabs.cdk import sila",
            "",
            ""
        ]

        # Generate execution errors
        for error in self.parser.execution_errors:
            code_lines.extend(self._generate_execution_error(error))
            code_lines.append("")

        # Generate custom data types
        for data_type in self.parser.data_types:
            code_lines.extend(self._generate_data_type(data_type))
            code_lines.append("")

        return "\n".join(code_lines)

    def _generate_execution_error(self, error: dict) -> list[str]:
        """Generate code for an execution error"""
        lines = []
        lines.append(f"class {error['identifier']}(sila.DefinedExecutionError):")
        lines.append('    """')
        lines.extend(format_docstring(error['description'], 4).split('\n'))
        lines.append('    """')
        return lines

    def _generate_data_type(self, data_type: dict) -> list[str]:
        """Generate code for a custom data type"""
        lines = []
        lines.append("@dataclasses.dataclass")
        lines.append(f"class {data_type['identifier']}(sila.CustomDataType):")
        lines.append('    """')
        lines.extend(format_docstring(data_type['description'], 4).split('\n'))

        # Add parameter documentation
        for element in data_type['definition']:
            lines.append("")
            lines.extend(format_docstring(f".. parameter:: {element['description']}", 4).split('\n'))

        lines.append('    """')
        lines.append("")

        # Generate fields
        for element in data_type['definition']:
            field_name = element['identifier']
            field_type = self._get_python_type(element['data_type'])
            lines.append(f"    {field_name}: {field_type}")

        return lines

    def _get_python_type(self, data_type_def: dict) -> str:
        """Convert data type definition to Python type annotation"""
        if data_type_def['type'] == 'basic':
            type_map = {
                'String': 'str',
                'Integer': 'int',
                'Real': 'float',
                'Boolean': 'bool'
            }
            return type_map.get(data_type_def['name'], 'str')

        elif data_type_def['type'] == 'custom':
            return data_type_def['name']

        elif data_type_def['type'] == 'list':
            inner_type = self._get_python_type(data_type_def['inner_type'])
            return f"list[{inner_type}]"

        elif data_type_def['type'] == 'constrained':
            base_type = self._get_python_type(data_type_def['base_type'])
            constraints = data_type_def.get('constraints', {})
            if 'min_inclusive' in constraints:
                return f"Annotated[{base_type}, sila.constraints.MinimalInclusive(value={constraints['min_inclusive']})]"
            return base_type

        raise ValueError(f"Unknown data type: {data_type_def}")


def main():
    parser = argparse.ArgumentParser(description='Generate feature_ul and sila_types from SiLA XML')
    parser.add_argument('xml_file', type=Path, help='Path to the SiLA XML file')
    parser.add_argument('--output-dir', type=Path, default=Path(''), help='Output directory for generated files')
    parser.add_argument('--feature-only', action='store_true', help='Generate only the feature file')
    parser.add_argument('--types-only', action='store_true', help='Generate only the sila_types file')

    args = parser.parse_args()

    if not args.xml_file.exists():
        print(f"Error: XML file {args.xml_file} does not exist")
        return 1

    # Parse the XML
    xml_parser = SiLAXMLParser(args.xml_file)

    # Generate feature_ul if requested
    if not args.types_only:
        feature_generator = FeatureGenerator(xml_parser)
        feature_code = feature_generator.generate_feature_ul()

        feature_filename = f"feature_ul.py"
        feature_path = args.output_dir / feature_filename

        with open(feature_path, 'w', encoding='utf-8') as f:
            f.write(feature_code)

        print(f"Generated feature file: {feature_path}")

    # Generate sila_types if requested
    if not args.feature_only:
        types_generator = SiLATypesGenerator(xml_parser)
        types_code = types_generator.generate_sila_types()

        types_dir = args.output_dir / "types"
        types_dir.mkdir(parents=True, exist_ok=True)  # Create the types directory if it doesn't exist
        types_path = types_dir / "sila_types.py"

        with open(types_path, 'w', encoding='utf-8') as f:
            f.write(types_code)

        print(f"Generated types file: {types_path}")

    return 0


if __name__ == '__main__':
    exit(main())
