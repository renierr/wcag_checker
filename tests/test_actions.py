import sys
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock
from src.actions.script_action import log_script
from src.config import ProcessingConfig
from src.ignore_violations import get_ignored_violations
from src.main import load_all_actions
from src.processing import handle_action


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
        load_all_actions()

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
        handle_action(self.config, mock_driver, action)
        mock_driver.execute_script.assert_called_once_with(
            log_script, 'This is a log message Demo.'
        )

    @patch('src.action_handler.action_context', new_callable=dict)
    @patch('selenium.webdriver.Chrome')
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_action(self, MockStdout, MockWebDriver, mock_action_context):
        mock_driver = MagicMock()
        MockWebDriver.return_value = mock_driver
        mock_action_context.update(self.context)
        action = {
            "name": "print",
            "params": 'This is a print message ${project}.'
        }
        handle_action(self.config, mock_driver, action)
        print_value = MockStdout.getvalue()
        self.assertIn('This is a print message Demo.\n', print_value)
        # Print to the real stdout
        sys.__stdout__.write(f"Catched Printed value: {print_value}\n")


    @patch('src.runner_contrast.take_fullpage_screenshot', return_value=None)
    @patch('src.actions.analyse_action.take_fullpage_screenshot', return_value=None)
    @patch('src.action_handler.action_context', new_callable=dict)
    @patch('selenium.webdriver.Chrome')
    def test_analyse_action(self, MockWebDriver, mock_action_context, mock_screenshot, mock_take_screenshot):
        mock_driver = MagicMock()
        MockWebDriver.return_value = mock_driver
        mock_driver.get_window_size.return_value = {"width": 1920, "height": 1080}
        mock_action_context.update(self.context)
        action = {
            "name": "analyse",
            "params": None
        }
        ret = handle_action(self.config, mock_driver, action)
        self.assertIsInstance(ret, dict)
        self.assertEqual(ret.get('violations', 0), 1, "The result should contain 1 violation")

    @patch('src.action_handler.action_context', new_callable=dict)
    @patch('selenium.webdriver.Chrome')
    def test_if_action(self, MockWebDriver, mock_action_context):
        mock_driver = MagicMock()
        MockWebDriver.return_value = mock_driver
        mock_action_context.update(self.context)
        action = {
            "type": "if",
            "name": "if",
            "condition": "true",
            "actions": [
                {
                    "name": "log",
                    "params": '"Condition is true, executing actions."'
                }
            ],
        }
        ret = handle_action(self.config, mock_driver, action)
        self.assertIsInstance(ret, list, "The return value should be a list")
        self.assertEqual(len(ret), 1, "The array should contain one action result")
        self.assertEqual(ret[0].get('name'), 'log', "The return value should contain the name 'log'")


    @patch('src.action_handler.action_context', new_callable=dict)
    @patch('selenium.webdriver.Chrome')
    def test_ignore_action(self, MockWebDriver, mock_action_context):
        mock_driver = MagicMock()
        MockWebDriver.return_value = mock_driver
        mock_action_context.update(self.context)
        action = {
            "name": "ignore",
            "params": 'ignore_this id with blanks'
        }
        handle_action(self.config, mock_driver, action)
        ignored_violations = get_ignored_violations()
        self.assertIn('ignore_this id with blanks', ignored_violations, "The violation should be added to the ignore list")

        # multiline ignore
        action = {
            "name": "ignore",
            "params": """{
            ignore_this
            another_one in another line
            multiple lines
            }"""
        }
        handle_action(self.config, mock_driver, action)
        self.assertIn('another_one in another line', ignored_violations, "The violation should be added to the ignore list (multiline)")

        # Print the ignored violations to stdout
        print(ignored_violations)


if __name__ == '__main__':
    unittest.main()
