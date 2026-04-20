"""Main script for step 1 of assignment 2."""

from assignment_2.step_1.bidding_model import DayAheadQuantityBiddingModel
from assignment_2.utils.data_loader import (
    load_da_prices,
    load_system_imbalance,
    load_wind_power,
)
from assignment_2.utils.scenario_creator import create_scenarios


def main() -> None:
    """Main function to run the optimization model."""
    capacity = 500.0
    in_sample_size = 200

    # Load data
    input_data = {
        "da_prices": load_da_prices(),
        "system_imbalance": load_system_imbalance(),
        "wind_power": load_wind_power(),
    }

    # Create scenarios
    scenarios = create_scenarios(input_data)
    weights: list[float] = [scenario["weight"] for scenario in scenarios]
    scenarios: list[dict[str, list[float]]] = [
        scenario["data"] for scenario in scenarios
    ]

    in_sample_scenarios = scenarios[:in_sample_size]
    out_of_sample_scenarios = scenarios[in_sample_size:]

    # Initialize and solve the optimization model
    one_price = DayAheadQuantityBiddingModel(
        capacity=capacity,
        scenarios=in_sample_scenarios,
        weights=weights,
        one_price_imbalance=True,
    )
    one_price.optimize()

    two_price = DayAheadQuantityBiddingModel(
        capacity=capacity,
        scenarios=in_sample_scenarios,
        weights=weights,
        one_price_imbalance=False,
    )
    two_price.optimize()

    print("In-sample results:")
    for i in range(24):
        print(
            f"Hour {i}: One-price bid = {one_price.vars['bid_quantity'][i].X:.2f}, "
            f"Two-price bid = {two_price.vars['bid_quantity'][i].X:.2f}"
        )


if __name__ == "__main__":
    main()
