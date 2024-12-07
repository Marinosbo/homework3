import logging
import re

class ConfigParser:
    def __init__(self):
        self.variables = {}
        logging.basicConfig(level=logging.DEBUG)

    def parse(self, text):
        lines = text.splitlines()
        result = {}
        config_lines = []
        in_config = False

        for line in lines:
            line = line.strip()
            if line.startswith("var"):
                self._parse_variable(line)
            elif line.startswith("config = $["):
                in_config = True
                config_lines.append(line[line.index("$[") + 2:].strip())
            elif in_config:
                if "]" in line:
                    config_lines.append(line.rstrip("]").strip())
                    in_config = False
                    config_content = " ".join(config_lines)
                    config_content = self._parse_variables_in_line(config_content)
                    result["config"] = self.parse_dict(config_content)
                else:
                    config_lines.append(line)
        logging.debug(f"Final config result: {result}")
        return result

    def _parse_variable(self, line):
        parts = line.split(' ', 2)
        if len(parts) < 3 or parts[0] != "var":
            raise ValueError(f"Некорректный синтаксис переменной: {line}")
        name = parts[1]
        value = parts[2].lstrip('=').strip()

        if value.startswith('@') and value.endswith('"'):
            self.variables[name] = value[2:-1]
        elif value.replace('.', '', 1).isdigit():
            self.variables[name] = float(value) if '.' in value else int(value)
        else:
            raise ValueError(f"Некорректное значение переменной: {value}")

    def _parse_variables_in_line(self, line):
        for var_name, var_value in self.variables.items():
            line = line.replace(f"^{{{var_name}}}", str(var_value))
        return line

    def parse_dict(self, text):
        items = re.split(r',\s*(?![^#]*\))', text)  # Исправление регулярного выражения
        result = {}
        for item in items:
            item = item.strip()
            if not item or ':' not in item:
                continue
            key, value = item.split(':', 1)
            key = key.strip()
            value = value.strip()

            if value.startswith('@') and value.endswith('"'):
                result[key] = value[2:-1]
            elif value.startswith("#(") and value.endswith(")"):
                result[key] = self.parse_array(value[2:-1].strip())
            elif value.replace('.', '', 1).isdigit():
                result[key] = int(value) if value.isdigit() else float(value)
            else:
                result[key] = value
        return result

    def parse_array(self, text):
        try:
            elements = text.split(',')
            array = []
            for element in elements:
                element = element.strip()
                if element.startswith('@') and element.endswith('"'):
                    array.append(element[2:-1])
                elif element.startswith("^{") and element.endswith("}"):
                    variable_name = element[2:-1].strip()
                    if variable_name not in self.variables:
                        raise ValueError(f"Переменная {variable_name} не найдена")
                    array.append(self.variables[variable_name])
                elif element.isdigit():
                    array.append(int(element))
                else:
                    raise ValueError(f"Некорректный элемент массива: {element}")
            return array
        except Exception as e:
            raise ValueError(f"Ошибка парсинга массива: {text}") from e

    def _remove_multiline_comments(self, text):
        return re.sub(r'\{-.*?-\}', '', text, flags=re.DOTALL)
