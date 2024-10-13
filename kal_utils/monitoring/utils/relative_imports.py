import os
import sys

# Need to be ignored in production

def add_parent_directory_to_sys_path(levels_up: int = 1):
    """
    Adds a directory `levels_up` levels above the current file to the sys.path.
    
    Args:
        levels_up (int): The number of directory levels to go up from the current file.
                         Defaults to 1.
    """
    current_file_directory = os.path.dirname(__file__)  # Directory of the current file
    target_directory = os.path.abspath(os.path.join(current_file_directory, *[".."] * levels_up))
    
    if target_directory not in sys.path:
        sys.path.insert(0, target_directory)

# Usage example:
# add_parent_directory_to_sys_path()  # Adds the directory one level up
