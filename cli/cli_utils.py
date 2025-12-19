import sys
import os

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

def format_path_with_gradient(display_dir: str) -> str:
    """
    Formats a path string with a color gradient for each segment.
    
    Args:
        display_dir: The path string to format (e.g. "~/workplace").
        
    Returns:
        Formatted string with ANSI color codes.
    """
    # Define gradient colors
    gradient_colors = [
        Color.BRIGHT_MAGENTA,
        Color.BRIGHT_BLUE,
        Color.CYAN,
        Color.BRIGHT_CYAN,
        Color.BRIGHT_GREEN
    ]
    separator_color = Color.BRIGHT_BLACK
    
    # Handle special root case or simple path
    if display_dir == "/" or display_dir == "~":
        return f"{gradient_colors[0]}{display_dir}{Color.RESET}"
    
    parts = display_dir.split(os.sep)
    colored_parts = []
    
    # Handle leading slash logic visually
    if display_dir.startswith(os.sep):
        colored_parts.append(f"{separator_color}/{Color.RESET}")
        
    real_parts = [p for p in parts if p]
    
    for i, part in enumerate(real_parts):
        color = gradient_colors[i % len(gradient_colors)]
        colored_parts.append(f"{color}{part}{Color.RESET}")
        
        # Add separator between parts (but not at end)
        if i < len(real_parts) - 1:
            colored_parts.append(f"{separator_color}/{Color.RESET}")
    
    return "".join(colored_parts)
