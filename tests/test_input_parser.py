import unittest
from unittest.mock import patch

import tempfile
import os
from pathlib import Path
from pprint import pprint

from src.action_handler import parse_param_to_key_value
from src.input_parser import _parse_config_file, parse_inputs

class TestParseConfigFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.logger_patcher = patch('src.input_parser.logger')
        cls.mock_logger = cls.logger_patcher.start()

        cls.mock_logger.debug.side_effect = lambda msg: print(f"DEBUG: {msg}")
        cls.mock_logger.info.side_effect = lambda msg: print(f"INFO: {msg}")
        cls.mock_logger.warning.side_effect = lambda msg: print(f"WARNING: {msg}")
        cls.mock_logger.error.side_effect = lambda msg: print(f"ERROR: {msg}")

    @classmethod
    def tearDownClass(cls):
        cls.logger_patcher.stop()

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
            # comment
            @navigate: /lalal/fgrg
            @click: #button
            @include: {include_f.name}
            @analyse_axe: {{"context": "test_context"}}
            @if "condition" {{
                @test
                @include: {include_f.name}
                @kkk
                @script: {{
                    let x = 5;
                }}
            }}
            
            # huhu
            @script: {{
                console.log("This is a test script");
            }}
            @wait: 5
            """
            f.write(fcontent)
            f.flush()

            inputs = ['input1', f'config:{f.name}', 'input3']
            result = parse_inputs(inputs)
            print_result(result)

            self.assertEqual(len(result), 10)

        os.unlink(f.name)
        os.unlink(include_f.name)

    def test_parse_simple_action(self):
        """Test parsing a simple action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            content = """
                @navigate: "http://improve-e2e.hype.qs/login?/servlet/hype"
            """
            f.write(content)
            f.flush()

            result = _parse_config_file(Path(f.name))
            print_result(result)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'action')
            self.assertEqual(result[0]['name'], 'navigate')
            self.assertIn('?', result[0]['params'])

        os.unlink(f.name)

    def test_parse_action_block_param(self):
        """Test parsing a simple action with block param"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            content = """
                @navigate: {
                    http://improve-e2e.hype.qs/login?/servlet/hype
                    # some stuff should be left inside
                    @lala
                }
            """
            f.write(content)
            f.flush()

            result = _parse_config_file(Path(f.name))
            print_result(result)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'action')
            self.assertEqual(result[0]['name'], 'navigate')
            self.assertIn('?', result[0]['params'])

        os.unlink(f.name)

    def test_parse_url(self):
        """Test parsing a url"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            content = """
                /this/is/a/url
                
                # comment ignored and another url
                http://example.com?a=b&b=c#ff@de
            """
            f.write(content)
            f.flush()

            result = _parse_config_file(Path(f.name))
            print_result(result)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]['type'], 'url')
            self.assertEqual(result[1]['type'], 'url')

        os.unlink(f.name)

    def test_parse_if_action(self):
        """Test parsing an if action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test = """
            @analyse_axe: {
                "context": "test_context",
                "options": {"option1": "value1"}
            }
            
            # comment1
            @var: myvar=5
            @if myvar == 5 {
                @navigate: "param2"
                @analyse
                @script: {
                    console.log("This is a test script");
                    const x = 5;
                    const y = {};
                    const z = ${myvar};
                }
            }
            @elif myvar == 1 {
                @navigate: "/login"
                @wait: 2
            }
            @elif myvar == "5" {
                @navigate: "/admin"
                
                # comment2
                @analyse_axe: {"context": "admin_panel"}
            }
            @else {
                @navigate: "/home"
                @script: {
                    console.log("Default behavior");
                }
            }
            """

            f.write(test)
            f.flush()

            result = _parse_config_file(Path(f.name))
            print_result(result)

            self.assertEqual(len(result), 3)
            self.assertEqual(result[2]['type'], 'if')
            self.assertEqual(result[2]['name'], 'if')
            self.assertIsInstance(result[2]['actions'], list)
            self.assertEqual(len(result[2]['actions']), 3)
            self.assertEqual(len(result[2]['elif_blocks']), 2)
            self.assertIsNotNone(result[2].get('else_actions'))

        os.unlink(f.name)

    def test_iframe_parse(self):
        """Test parsing an iframe action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test = """
            @iframe #my_iframe {
                @analyse_axe: {"context": "#dashboard"}
            }
            """

            f.write(test)
            f.flush()

            result = _parse_config_file(Path(f.name))
            print_result(result)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'iframe')
            self.assertEqual(result[0]['name'], 'iframe')
            self.assertIsInstance(result[0]['actions'], list)
            self.assertEqual(len(result[0]['actions']), 1)

        os.unlink(f.name)

    def test_file_not_found(self):
        """Test handling of non-existent file"""
        result = _parse_config_file(Path('non_existent_file.txt'))
        self.assertEqual(result, [])
        self.mock_logger.warning.assert_called_once()

    def test_empty_file(self):
        """Test parsing empty file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('')
            f.flush()

            result = _parse_config_file(Path(f.name))
            self.assertEqual(result, [])

        os.unlink(f.name)

    def test_includes(self):
        """Test parsing includes"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as include_f:
            inc_content = """
            @navigate: "/lalal/eeee"
            @var: myvar="5"
            @wait: 4
            @include: ../another_include.txt
            """
            include_f.write(inc_content)
            include_f.flush()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            includename_only = os.path.basename(include_f.name)
            fcontent = f"""
            @navigate: /lalal/fgrg
            @click: #button
            @include: {includename_only}
            """
            f.write(fcontent)
            f.flush()

            result = _parse_config_file(Path(f.name))
            print_result(result)
            self.assertEqual(len(result), 5)
            self.mock_logger.warning.assert_called()

    def test_example_actions(self):
        """Test parsing example actions"""
        inputs = ['config:../example.actions']
        result = parse_inputs(inputs)
        print_result(result)

        self.assertGreater(len(result), 1)

    def test_parse_param_to_key_value(self):
        """Test parsing a key-value pair"""
        content = "my.variable=my_value"

        key, value = parse_param_to_key_value(content)
        self.assertEqual(key, 'my.variable')
        self.assertEqual(value, 'my_value')

        key, value = parse_param_to_key_value("my_variable")
        self.assertIsNone(key)
        self.assertEqual(value, 'my_variable')


def print_result(result):
    """Helper function to print the result in a readable format."""
    print("=" * 80)
    for i, item in enumerate(result):
        print(f"Item {i}:")
        pprint(item)
        print()

if __name__ == '__main__':
    unittest.main()
