import unittest
from unittest.mock import patch, MagicMock
from src.actions.script_action import log_action, log_script
from src.config import ProcessingConfig

class TestActions(unittest.TestCase):

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
        self.config = ProcessingConfig()

    @patch('src.action_handler.action_context', new_callable=dict)
    @patch('selenium.webdriver.Chrome')
    def test_log_action(self, MockWebDriver, mock_action_context):
        mock_driver = MagicMock()
        MockWebDriver.return_value = mock_driver
        mock_action_context.update(self.context)
        action = {
            "name": "log",
            "params": '"This is a log message ${project}."'
        }
        log_action(self.config, mock_driver, action)
        mock_driver.execute_script.assert_called_once_with(
            log_script, 'This is a log message Demo.'
        )


if __name__ == '__main__':
    unittest.main()
