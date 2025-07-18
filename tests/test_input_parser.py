import unittest
import tempfile
import os
from pprint import pprint
from src.input_parser import _parse_config_file, parse_inputs


class TestParseConfigFile(unittest.TestCase):

    def test_inputs(self):
        """Test parsing inputs"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as include_f:
            inc_content = """
            @navigate: /lalal/eeee
            @wait: 4
            """
            include_f.write(inc_content)
            include_f.flush()


        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            fcontent = f"""
            @navigate: /lalal/fgrg
            @click: #button
            @include: {include_f.name}
            @analyse_axe: {{"context": "test_context"}}
            @if: "condition" : {{
                @test
                @include: {include_f.name}
                @kkk
                @script: {{
                    let x = 5;
                }}
            }}
            @script: {{
                console.log("This is a test script");
            }}
            @wait: 5
            """
            f.write(fcontent)
            f.flush()

            inputs = ['input1', f'config:{f.name}', 'input3']
            result = parse_inputs(inputs)
            pprint(result)

        os.unlink(f.name)
        os.unlink(include_f.name)


    def test_parse_simple_action(self):
        """Test parsing a simple action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('@wait: 5')
            f.flush()

            result = _parse_config_file(f.name)
            pprint(result)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'action')
            self.assertEqual(result[0]['name'], 'wait')
            self.assertEqual(result[0]['params'], '5')

        os.unlink(f.name)

    def test_parse_if_action(self):
        """Test parsing an if action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test = """
            @analyse_axe: {
                "context": "test_context",
                "options": {"option1": "value1"}
            }
            @if: "condition" : {
                @navigate: "param2"
                @analyse
                @script: {
                    console.log("This is a test script");
                    const x = 5;
                    const y = {};
                }
            }
            """

            f.write(test)
            f.flush()

            result = _parse_config_file(f.name)
            pprint(result)

            self.assertEqual(len(result), 2)
            self.assertEqual(result[1]['type'], 'if')
            self.assertEqual(result[1]['name'], 'if')
            self.assertIsInstance(result[1]['actions'], list)
            self.assertEqual(len(result[1]['actions']), 3)

        os.unlink(f.name)

    def test_file_not_found(self):
        """Test handling of non-existent file"""
        result = _parse_config_file('non_existent_file.txt')
        self.assertEqual(result, [])

    def test_empty_file(self):
        """Test parsing empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('')
            f.flush()

            result = _parse_config_file(f.name)
            self.assertEqual(result, [])

        os.unlink(f.name)

if __name__ == '__main__':
    unittest.main()
