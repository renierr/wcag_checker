
class ConsoleLogEntry:
    def __init__(self, level, text, timestamp, type):
        self.level = level
        self.text = text
        self.timestamp = timestamp
        self.type = type

    def to_dict(self):
        return {
            "level": self.level,
            "text": self.text,
            "timestamp": self.timestamp
        }

browser_console_log = []
def handle_browser_console_log(log_message):
    """
    Handles browser console log messages by printing them to the console.

    Args:
        log_message (str): The log message to be printed.
    """
    entry = {
        "level": getattr(log_message, "level", None),
        "text": getattr(log_message, "text", None),
        "timestamp": getattr(log_message, "timestamp", None),
        "type": getattr(log_message, "type_", None)
    }
    browser_console_log.append(entry)

def get_browser_console_log():
    """
    Returns the browser console log messages.

    Returns:
        list: A list of browser console log messages.
    """
    return browser_console_log
