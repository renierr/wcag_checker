import unittest
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


if __name__ == '__main__':
    unittest.main()