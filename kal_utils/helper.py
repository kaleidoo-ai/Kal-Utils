def validate_dict_structure(data: dict, expected_data: dict, check_extra_keys: bool = False) -> bool:
    """
    Validate that all expected data is present and not empty, and optionally check for extra keys.

    Parameters:
    - data (dict): A dictionary containing the actual data to validate.
    - expected_data (dict): A dictionary containing the expected data structure.
    - check_extra_keys (bool): A boolean flag indicating whether to check for extra keys in the data.
                               Default is False.

    Returns:
    - bool: True if validation passes, False otherwise.
    """
    # Check for missing or empty values
    for key in expected_data.keys():
        if not data.get(key):
            return False

    if check_extra_keys:
        # Check for extra keys
        for key in data.keys():
            if key not in expected_data:
                return False

    return True
