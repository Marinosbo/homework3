import unittest
from parser import ConfigParser

class TestConfigParser(unittest.TestCase):
    def setUp(self):
        self.parser = ConfigParser()

    def _parse_variable(self, line):
        # Разбираем строку, ожидаем формат: var имя = значение
        parts = line.split(' ', 2)
        if len(parts) < 3 or parts[0] != "var":
            raise ValueError(f"Некорректный синтаксис переменной: {line}")

        name = parts[1]  # Имя переменной
        value = parts[2].lstrip('=').strip()  # Убираем '=' и лишние пробелы

        # Проверяем наличие '=' в значении переменной
        if '=' not in value:
            raise ValueError(f"Некорректное значение переменной: {line}")

        # Проверяем тип значения
        if value.startswith('@') and value.endswith('"'):  # Строка
            self.variables[name] = value[2:-1]  # Убираем @ и кавычки
        elif value.isdigit():  # Целое число
            self.variables[name] = int(value)
        elif value.replace('.', '', 1).isdigit():  # Число с плавающей точкой
            self.variables[name] = float(value)
        else:
            raise ValueError(f"Некорректное значение переменной: {value}")

    def test_parse_array(self):
        array = self.parser.parse_array('@"home", @"login", @"dashboard"')
        self.assertEqual(array, ["home", "login", "dashboard"])

    def test_parse_dict(self):
        dictionary = self.parser.parse_dict('address: @"localhost", port: 8080')
        self.assertEqual(dictionary, {"address": "localhost", "port": 8080})

    def to_toml(self, data, indent=2):
        def format_value(value, current_indent):
            if isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, list):
                return f"[{', '.join(format_value(v, current_indent) for v in value)}]"
            elif isinstance(value, dict):
                inner_indent = current_indent + indent
                formatted_items = ",\n".join(
                    f"{' ' * inner_indent}{k} = {format_value(v, inner_indent)}"
                    for k, v in value.items()
                )
                return "{\n" + formatted_items + f"\n{' ' * current_indent}}}"
            else:
                return str(value)

        return "config = " + format_value(data, indent)

    def test_full_parsing(self):
        input_text = '''
        var host = @"localhost"
        var port = 8080
        config = $[
            address: ^{host},
            port: ^{port},
            paths: #( @"home", @"login", @"dashboard" )
        ]
        '''
        expected_result = {
            "config": {
                "address": "localhost",
                "port": 8080,
                "paths": ["home", "login", "dashboard"]
            }
        }
        parsed_data = self.parser.parse(input_text)
        self.assertEqual(parsed_data, expected_result)


if __name__ == '__main__':
    unittest.main()
