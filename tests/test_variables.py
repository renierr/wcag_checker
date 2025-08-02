import unittest
from unittest.mock import patch
from src.action_handler import parse_param_to_string, parse_param_to_dict, parse_param_to_key_value
from src.config import ProcessingConfig
from src.utils import resolve_var

class TestVariables(unittest.TestCase):

    def setUp(self):
        """Set up common context for tests"""
        self.context = {
            "user": {
                "name": "Alice",
                "details": {
                    "age": 30
                }
            },
            "project": "Demo"
        }

    def test_resolve(self):
        """Test resolve function with nested variables"""
        text = "Hello ${user.name}, your age is ${user.details.age}. Welcome to ${project}!"
        expected = "Hello Alice, your age is 30. Welcome to Demo!"
        self.assertEqual(resolve_var(self.context, text), expected)

    def test_resolve_with_brackets(self):
        """Test resolve function with nested variables"""
        text = "Hello ${user.name}, this is ok {normal}"
        expected = "Hello Alice, this is ok {normal}"
        self.assertEqual(resolve_var(self.context, text), expected)

    def test_resolve_with_missing_variable(self):
        """Test resolve function with a missing variable"""
        text = "Hello ${user.name}, your age is ${user.details.age}. Welcome to ${project} and ${missing}!"
        expected = "Hello Alice, your age is 30. Welcome to Demo and !"
        self.assertEqual(resolve_var(self.context, text), expected)

    def test_resolve_with_empty_context(self):
        """Test resolve function with an empty context"""
        text = "Hello ${user.name}, welcome to ${project}!"
        expected = "Hello , welcome to !"
        self.assertEqual(resolve_var({}, text), expected)

    def test_resolve_with_no_variables(self):
        """Test resolve function with no variables in text"""
        text = "Hello Alice, welcome to the project!"
        expected = "Hello Alice, welcome to the project!"
        self.assertEqual(resolve_var(self.context, text), expected)

    @patch('src.action_handler.action_context', new_callable=dict)
    def test_resolve_for_string_param(self, mock_action_context):
        mock_action_context.update(self.context)
        text = parse_param_to_string("Hello ${user.name}, Welcome to ${project}!")
        expected = "Hello Alice, Welcome to Demo!"
        self.assertEqual(expected, text)

    @patch('src.action_handler.action_context', new_callable=dict)
    def test_resolve_for_dict_param(self, mock_action_context):
        mock_action_context.update(self.context)
        text = parse_param_to_dict("""{"context": "Hello ${user.name}"}""")
        expected = {"context": "Hello Alice"}
        self.assertEqual(expected, text)

    @patch('src.action_handler.action_context', new_callable=dict)
    def test_resolve_for_key_value_param(self, mock_action_context):
        mock_action_context.update(self.context)
        key, value = parse_param_to_key_value("""key=${user.name}""")
        self.assertEqual("key", key)
        self.assertEqual("Alice", value)

    def test_var_action_setting(self):
        """Test setting a variable in the context"""
        from src.actions.variables_action import var_action
        action = {"params": "my.variable=my_value"}
        var_action(None, None, action, self.context)
        print(self.context)
        self.assertEqual(self.context["my"]["variable"], "my_value")

    def test_resolve_with_class(self):
        pc = ProcessingConfig()
        context = { "config": pc }
        text = "Hello ${config.output}"
        expected = "Hello output"
        self.assertEqual(expected, resolve_var(context, text))

    def test_var_default_action_setting(self):
        """Test setting a default variable in the context"""
        from src.actions.variables_action import var_default_action
        action = {"params": "my.variable=default_value"}
        var_default_action(None, None, action, self.context)
        self.assertEqual(self.context["my"]["variable"], "default_value")

        # Test that it does not overwrite an existing variable
        action = {"params": "my.variable=another_value"}
        var_default_action(None, None, action, self.context)
        self.assertEqual(self.context["my"]["variable"], "default_value")

if __name__ == '__main__':
    unittest.main()
