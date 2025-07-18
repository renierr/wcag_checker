import unittest
from src.actions.if_action import _eval_condition


class TestConditionParser(unittest.TestCase):

    def test_boolean_literals(self):
        """Test basic boolean values"""
        self.assertTrue(_eval_condition("true"))
        self.assertFalse(_eval_condition("false"))

    def test_boolean_operations(self):
        """Test AND, OR, NOT operations"""
        self.assertTrue(_eval_condition("true and true"))
        self.assertFalse(_eval_condition("true and false"))
        self.assertTrue(_eval_condition("true or false"))
        self.assertFalse(_eval_condition("false or false"))
        self.assertFalse(_eval_condition("not true"))
        self.assertTrue(_eval_condition("not false"))

    def test_comparison_operations(self):
        """Test equality and inequality operations"""
        # Equality
        self.assertTrue(_eval_condition("5 == 5"))
        self.assertFalse(_eval_condition("5 == 3"))
        self.assertTrue(_eval_condition("\"hello\" == \"hello\""))

        # Inequality
        self.assertTrue(_eval_condition("5 != 3"))
        self.assertFalse(_eval_condition("5 != 5"))

        # Numeric comparisons
        self.assertTrue(_eval_condition("10 > 5"))
        self.assertFalse(_eval_condition("5 > 10"))
        self.assertTrue(_eval_condition("5 < 10"))
        self.assertTrue(_eval_condition("5 >= 5"))
        self.assertTrue(_eval_condition("5 <= 5"))

    def test_string_operations(self):
        """Test string contains operations"""
        self.assertTrue(_eval_condition("\"hello world\" contains \"world\""))
        self.assertFalse(_eval_condition("\"hello\" contains \"world\""))
        self.assertTrue(_eval_condition("\"test\" contains \"es\""))

    def test_membership_operations(self):
        """Test 'in' operations with context"""
        context = {"roles": ["admin", "user"], "user_type": "admin"}
        self.assertTrue(_eval_condition("\"admin\" in roles", context))
        self.assertFalse(_eval_condition("\"guest\" in roles", context))

    def test_variables_with_context(self):
        """Test variable resolution with context"""
        context = {
            "is_logged_in": True,
            "user_active": False,
            "age": 25,
            "name": "John",
            "status": "active"
        }
        self.assertTrue(_eval_condition("is_logged_in", context))
        self.assertFalse(_eval_condition("user_active", context))
        self.assertTrue(_eval_condition("age > 18", context))
        self.assertTrue(_eval_condition("name == \"John\"", context))
        self.assertTrue(_eval_condition("status == \"active\"", context))

    def test_nested_context_access(self):
        """Test accessing nested context properties"""
        context = {
            "user": {
                "profile": {
                    "name": "Alice",
                    "age": 30
                },
                "permissions": ["read", "write"]
            },
            "session": {
                "active": True,
                "timeout": 3600
            }
        }
        self.assertTrue(_eval_condition("user.profile.name == \"Alice\"", context))
        self.assertTrue(_eval_condition("user.profile.age >= 25", context))
        self.assertTrue(_eval_condition("session.active", context))
        self.assertTrue(_eval_condition("\"write\" in user.permissions", context))

    def test_context_with_complex_conditions(self):
        """Test complex conditions with context"""
        context = {
            "user": {
                "age": 25,
                "role": "admin",
                "active": True
            },
            "request": {
                "method": "POST",
                "path": "/api/users",
                "authenticated": True
            },
            "system": {
                "maintenance": False,
                "load": 0.3
            }
        }

        # User authorization check
        condition1 = "user.active and user.role == \"admin\" and request.authenticated"
        self.assertTrue(_eval_condition(condition1, context))

        # System health check
        condition2 = "not system.maintenance and system.load < 0.8"
        self.assertTrue(_eval_condition(condition2, context))

        # Complex access control
        condition3 = "(user.role == \"admin\" or user.role == \"moderator\") and user.age >= 18"
        self.assertTrue(_eval_condition(condition3, context))

    def test_missing_context_variables(self):
        """Test handling of missing context variables"""
        context = {"existing_var": True}

        # Should handle missing variables gracefully
        with self.assertRaises(NameError):
            _eval_condition("missing_var", context)

        with self.assertRaises(NameError):
            _eval_condition("existing_var and missing_var", context)

    def test_context_type_validation(self):
        """Test type validation with context"""
        context = {
            "count": 10,
            "name": "test",
            "active": True,
            "scores": [85, 90, 78]
        }

        # Numeric operations
        self.assertTrue(_eval_condition("count > 5", context))
        self.assertFalse(_eval_condition("count < 5", context))

        # String operations
        self.assertTrue(_eval_condition("name contains \"es\"", context))
        self.assertTrue(_eval_condition("name == \"test\"", context))

        # Boolean operations
        self.assertTrue(_eval_condition("active and count > 0", context))

        # Array operations
        self.assertTrue(_eval_condition("85 in scores", context))
        self.assertFalse(_eval_condition("95 in scores", context))

    def test_dynamic_context_updates(self):
        """Test parser with dynamically updated context"""
        context = {"status": "pending", "attempts": 0}

        self.assertTrue(_eval_condition("status == \"pending\"", context))
        self.assertTrue(_eval_condition("attempts == 0", context))

        # Update context
        context["status"] = "completed"
        context["attempts"] = 3

        self.assertTrue(_eval_condition("status == \"completed\"", context))
        self.assertTrue(_eval_condition("attempts > 0", context))

    def test_empty_context(self):
        """Test parser with empty context"""
        # Should work with literals
        self.assertTrue(_eval_condition("true"))
        self.assertTrue(_eval_condition("5 > 3"))
        self.assertTrue(_eval_condition("\"hello\" == \"hello\""))

        # Should fail with variables
        with self.assertRaises(NameError):
            _eval_condition("some_var", {})

    def test_context_with_special_characters(self):
        """Test context with special characters in keys/values"""
        context = {
            "user_name": "test@example.com",
            "api_key": "abc-123-def",
            "message": "Hello, World!",
            "config.debug": True
        }

        self.assertTrue(_eval_condition("user_name contains \"@\"", context))
        self.assertTrue(_eval_condition("api_key contains \"-\"", context))
        self.assertTrue(_eval_condition("message contains \"!\"", context))


if __name__ == '__main__':
    unittest.main()