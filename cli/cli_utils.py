import sys

class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

class Cursor:
    # Erase functions
    ERASE_DISPLAY = "\033[2J"
    ERASE_LINE = "\033[2K"

def _print_formatted_message(
    message: str,
    prefix: str = "",
    color: str = "",
    style: str = "",
    stream=sys.stdout,
    end: str = "\n"
):
    """
    Prints a formatted message to the specified stream.
    """
    formatted_message = f"{style}{color}{prefix}{message}{Color.RESET}{end}"
    stream.write(formatted_message)
    stream.flush()
