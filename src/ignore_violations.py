from pathlib import Path
from src.logger_setup import logger

ignored_violations = set()

def get_ignored_violations() -> set[str]:
    """
    Get the set of ignored violation IDs.

    :return: A set containing the ignored violation IDs.
    """
    return ignored_violations

def populate_ignored_violation_from_file(file_path: Path | None):
    """
    Populate the ignored_violations list from a file.

    This function reads a file line by line, ignoring empty lines and comments,
    and adds the violation IDs to the ignored_violations set.

    :param file_path: Path to the file containing ignored violation IDs.
    """

    if file_path is None:
        return

    if not file_path.exists():
        logger.warning(f"File {file_path} does not exist. Skipping loading ignored violations.")
        return

    try:
        with file_path.open('r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):  # Ignore empty lines and comments
                    ignored_violations.add(line)
        logger.info(f"Loaded ignored violations: {len(ignored_violations)}")
    except Exception as e:
        logger.error(f"Error reading ignored violations file {file_path}: {e}")


def add_ignore_violation(violation_id: str):
    if violation_id:
        ignored_violations.add(violation_id)


def violation_ignored(violation_id: str) -> bool:
    """
    Check if a violation ID is in the ignored violations set.

    :param violation_id: The violation ID to check.
    :return: True if the violation ID is ignored, False otherwise.
    """
    if isinstance(violation_id, list):
        violation_id = tuple(violation_id)
    return violation_id in ignored_violations
