"""Script for combining input data into sceanrios."""

from itertools import product


def create_scenarios(
    input_data: dict[str, dict[str, list[float]]],
) -> list[dict[str, float | dict[str, list[float]]]]:
    """Create all scenarios for step 1 of assignment 2.

    Args:
        input_data (dict[str, dict[str, list[float]]]): A dictionary containing the input data for each scenario.

    Returns:
        list[dict[str, float | dict[str, list[float]]]]: A list of all scenarios, and their weights. Set equal for all scenarios.
    """
    data_keys = list(input_data.keys())
    result: list[dict[str, float | dict[str, list[float]]]] = [
        {
            "weight": 1.0,
            "data": {
                data_key: values
                for data_key, (_, values) in zip(
                    data_keys, scenario_combination, strict=True
                )
            },
        }
        for scenario_combination in product(
            *(scenario_data.items() for scenario_data in input_data.values())
        )
    ]

    return result


if __name__ == "__main__":
    from assignment_2.utils.data_loader import (
        load_da_prices,
        load_system_imbalance,
        load_wind_power,
    )

    input_data = {
        "wind_power": load_wind_power(),
        "da_prices": load_da_prices(),
        "system_imbalance": load_system_imbalance(),
    }
    scenarios = create_scenarios(input_data)

    print(f"Created {len(scenarios)} scenarios.")
    pass
