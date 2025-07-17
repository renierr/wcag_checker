import unittest
import tempfile
import os
from src.input_parser import _parse_config_file, parse_inputs


class TestParseConfigFile(unittest.TestCase):

    def test_inputs(self):
        """Test parsing inputs"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            fcontent = """
            @navigate: /lalal/fgrg
            @click: #button
            @include: C:\\dev\\python\\wcag_checker\\inputs.txt
            @if: "condition" : {
                @test
                @include: C:\\dev\\python\\wcag_checker\\inputs.txt
                @kkk
                @script: {
                    @dd: fff
                }
            }
            @script: {
                @dd: fff
            }
            @wait: 5
            """
            f.write(fcontent)
            f.flush()

            inputs = ['input1', f'config:{f.name}', 'input3']
            result = parse_inputs(inputs)
            print(result)

        os.unlink(f.name)


    def test_parse_simple_action(self):
        """Test parsing a simple action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('@include: C:\\dev\\python\\wcag_checker\\inputs.txt')
            f.flush()

            result = _parse_config_file(f.name)
            print(result)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'action')
            self.assertEqual(result[0]['name'], 'download')
            self.assertEqual(result[0]['params'], ['https://example.com'])

        os.unlink(f.name)

    def test_parse_if_action(self):
        """Test parsing an if action"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            test = """
            @if: "condition" : {
                @test
                @include: "param2"
                @kkk
                @script: {
                    @dd: fff
                }
            }
            """

            f.write(test)
            f.flush()

            result = _parse_config_file(f.name)
            print(result)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['type'], 'if')
            self.assertEqual(result[0]['name'], 'if')
            self.assertEqual(result[0]['params'][0], 'condition')
            self.assertIsInstance(result[0]['params'][1], list)

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
