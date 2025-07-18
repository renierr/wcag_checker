import unittest
import tempfile
import os
from pathlib import Path
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
            # comment
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
            pprint(result)

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
            pprint(result)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'action')
            self.assertEqual(result[0]['name'], 'navigate')
            self.assertIn('?', result[0]['params'])

        os.unlink(f.name)

    def test_parse_if_action(self):
        """Test parsing an if action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test = """
            @analyse_axe: {
                "context": "test_context",
                "options": {"option1": "value1"}
            }
            
            # comment
            @var: myvar=5
            @if: myvar == 5 : {
                @navigate: "param2"
                @analyse
                @script: {
                    console.log("This is a test script");
                    const x = 5;
                    const y = {};
                    const z = ${myvar};
                }
            }
            @elif: myvar == 1 : {
                @navigate: "/login"
                @wait: 2
            }
            @elif: myvar == "5" : {
                @navigate: "/admin"
                @analyse_axe: {"context": "admin_panel"}
            }
            @else: {
                @navigate: "/home"
                @script: {
                    console.log("Default behavior");
                }
            }
            """

            f.write(test)
            f.flush()

            result = _parse_config_file(Path(f.name))
            pprint(result)

            self.assertEqual(len(result), 3)
            self.assertEqual(result[2]['type'], 'if')
            self.assertEqual(result[2]['name'], 'if')
            self.assertIsInstance(result[2]['actions'], list)
            self.assertEqual(len(result[2]['actions']), 3)

        os.unlink(f.name)

    def test_file_not_found(self):
        """Test handling of non-existent file"""
        result = _parse_config_file(Path('non_existent_file.txt'))
        self.assertEqual(result, [])

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
            pprint(result)

if __name__ == '__main__':
    unittest.main()
