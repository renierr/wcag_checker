
browser_console_log = []
def handle_browser_console_log(log_message):
    entry = {
        "level": getattr(log_message, "level", None),
        "text": getattr(log_message, "text", None),
        "timestamp": getattr(log_message, "timestamp", None),
        "type": getattr(log_message, "type_", None)
    }
    browser_console_log.append(entry)

def get_browser_console_log() -> list[dict]:
    """
    Returns the browser console log messages as dict.

    This function collects all console log entries that have been captured
    during the browser session and returns them as a list of dictionaries.
    Each dictionary contains the log level, text, timestamp, and type of the log entry.
    If no log entries have been captured, an empty list is returned.

    :return: List of dictionaries containing console log entries.
    """
    return browser_console_log
