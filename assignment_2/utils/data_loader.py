"""Functions for loading data for the assignment."""

import json


def load_json_file(file_path: str) -> dict[str, list[float]]:
    """Load a json file and return its content as a dictionary.

    Args:
        file_path (str): The path to the json file.

    Returns:
        dict[str, list[float]]: The content of the json file as a dictionary.
    """
    with open(file_path) as f:
        data = json.load(f)

    return {
        key: [
            float(value) if isinstance(value, (int, bool)) else value
            for value in values
        ]
        for key, values in data.items()
    }


def load_da_prices() -> dict[str, list[float]]:
    """Load the day-ahead price forecast from the json file."""
    return load_json_file("assignment_2/data/da_prices.json")


def load_wind_power() -> dict[str, list[float]]:
    """Load the wind power forecast from the json file."""
    return load_json_file("assignment_2/data/wind_power.json")


def load_system_imbalance() -> dict[str, list[float]]:
    """Load the system imbalance forecast from the json file."""
    return load_json_file("assignment_2/data/system_imbalance.json")
