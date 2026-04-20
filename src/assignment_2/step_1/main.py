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

    in_sample_scenarios = scenarios[:in_sample_size]
    out_of_sample_scenarios = scenarios[in_sample_size:]

    # Initialize and solve the optimization model
    model = DayAheadQuantityBiddingModel(
        capacity=capacity, scenarios=in_sample_scenarios, one_price_imbalance=False
    )
    model.optimize()

    print("Optimal bid quantities for each hour:")
    for hour, quantity in enumerate(model.bid_quantities):
        print(f"Hour {hour}: {quantity}")


if __name__ == "__main__":
    main()
