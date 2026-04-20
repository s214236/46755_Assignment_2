"""Script for combining input data into sceanrios."""

from itertools import product


def create_scenarios(
    input_data: list[dict[str, list[float]]],
) -> list[dict[str, float | dict[str, list[float]]]]:
    """Create all scenarios for step 1 of assignment 2.

    Args:
        input_data (list[dict[str, list[float]]]): A list of dictionaries,
            each containing a key and a list of 24 values.

    Returns:
        list[dict[str, float | dict[str, list[float]]]]: A list of all scenarios, and their weights. Set equal for all scenarios.
    """
    result: list[dict[str, float | dict[str, list[float]]]] = [
        {
            "weight": 1.0,
            "data": {
                "wind_forecast": wind,
                "da_price_forecast": da_price,
                "system_imbalance_forecast": system_imbalance,
            },
        }
        for wind, da_price, system_imbalance in product(
            *[data.values() for data in input_data]
        )
    ]

    return result


if __name__ == "__main__":
    from assignment_2.utils.data_loader import (
        load_da_prices,
        load_system_imbalance,
        load_wind_power,
    )

    input_data = [load_wind_power(), load_da_prices(), load_system_imbalance()]
    scenarios = create_scenarios(input_data)

    print(f"Created {len(scenarios)} scenarios.")
    pass
