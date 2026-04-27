"""Main script for step 1 of assignment 2."""

import time

import matplotlib.pyplot as plt
import numpy as np

from assignment_2.step_1.bidding_model import (
    DayAheadQuantityBiddingModel,
    RiskAverseDayAheadQuantityBiddingModel,
)
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
    in_sample_weights = weights[:in_sample_size]
    out_of_sample_scenarios = scenarios[in_sample_size:]

    # Initialize and solve the optimization model
    one_price = DayAheadQuantityBiddingModel(
        capacity=capacity,
        scenarios=in_sample_scenarios,
        weights=in_sample_weights,
        one_price_imbalance=True,
    )
    one_price.optimize()

    two_price = DayAheadQuantityBiddingModel(
        capacity=capacity,
        scenarios=in_sample_scenarios,
        weights=in_sample_weights,
        one_price_imbalance=False,
    )
    two_price.optimize()

    print("In-sample results:")
    for i in range(24):
        print(
            f"Hour {i}: One-price bid = {one_price.bid_quantities[i]}, "
            f"Two-price bid = {two_price.bid_quantities[i]}"
        )
    print("Expected profit (one-price):", one_price.expected_profit)
    print("Expected profit (two-price):", two_price.expected_profit)

    plt.figure(figsize=(12, 6))
    plt.plot(one_price.bid_quantities, label="One-price Bids", marker="o")
    plt.plot(two_price.bid_quantities, label="Two-price Bids", marker="s")
    plt.xlabel("Hour")
    plt.ylabel("Bid Quantity [MWh]")
    plt.title("Bidding Results")
    plt.legend()
    plt.show()

    one_price_scenarios_profit, two_price_scenarios_profit = (
        list(x)
        for x in zip(
            *sorted(
                zip(one_price.scenarios_profit, two_price.scenarios_profit, strict=True)
            ),
            strict=True,
        )
    )
    plt.figure(figsize=(12, 6))
    plt.plot(one_price_scenarios_profit, label="One-price Scenarios", marker="o")
    plt.plot(two_price_scenarios_profit, label="Two-price Scenarios", marker="s")
    plt.xlabel("Scenario")
    plt.ylabel("Profit [EUR]")
    plt.title("Profit Results")
    plt.legend()
    plt.show()

    # %% Ex-post analysis
    input("Press Enter to start ex-post analysis...")
    print("\nStarting ex-post analysis...")

    in_sample_profit_one_price = []
    out_of_sample_profit_one_price = []
    in_sample_profit_two_price = []
    out_of_sample_profit_two_price = []
    i = 0
    runtime_start = time.time()
    while i < len(scenarios):
        in_sample_scenarios = scenarios[i : i + in_sample_size]
        in_sample_weights = weights[i : i + in_sample_size]
        out_of_sample_scenarios = scenarios[:i] + scenarios[i + in_sample_size :]

        one_price = DayAheadQuantityBiddingModel(
            capacity=capacity,
            scenarios=in_sample_scenarios,
            weights=in_sample_weights,
            one_price_imbalance=True,
        )
        one_price.optimize()
        two_price = DayAheadQuantityBiddingModel(
            capacity=capacity,
            scenarios=in_sample_scenarios,
            weights=in_sample_weights,
            one_price_imbalance=False,
        )
        two_price.optimize()

        in_sample_profit_one_price.append(one_price.expected_profit)
        out_of_sample_profit_one_price.append(
            one_price.out_of_sample_profit(out_of_sample_scenarios)
        )
        in_sample_profit_two_price.append(two_price.expected_profit)
        out_of_sample_profit_two_price.append(
            two_price.out_of_sample_profit(out_of_sample_scenarios)
        )

        i += in_sample_size

    runtime_end = time.time()
    print(f"Runtime for ex-post analysis: {runtime_end - runtime_start:.2f} seconds")

    print("Ex-post analysis results:")
    mean_in_sample_profit_one_price = sum(in_sample_profit_one_price) / len(
        in_sample_profit_one_price
    )
    mean_out_of_sample_profit_one_price = sum(out_of_sample_profit_one_price) / len(
        out_of_sample_profit_one_price
    )
    mean_in_sample_profit_two_price = sum(in_sample_profit_two_price) / len(
        in_sample_profit_two_price
    )
    mean_out_of_sample_profit_two_price = sum(out_of_sample_profit_two_price) / len(
        out_of_sample_profit_two_price
    )
    print(f"One-price mean in-sample profit: {mean_in_sample_profit_one_price:.2f}")
    print(
        f"One-price mean out-of-sample profit: {mean_out_of_sample_profit_one_price:.2f}"
    )
    print(f"Two-price mean in-sample profit: {mean_in_sample_profit_two_price:.2f}")
    print(
        f"Two-price mean out-of-sample profit: {mean_out_of_sample_profit_two_price:.2f}"
    )

    # %% Risk-Averse offering strategy
    input("Press Enter to start Risk-Averse offering strategy...")
    print("\nStarting Risk-Averse offering strategy...")

    alpha = 0.90
    res = 0.05
    betas = np.arange(0.0, 1 + res, res)

    in_sample_scenarios = scenarios[:in_sample_size]
    in_sample_weights = weights[:in_sample_size]

    cvars_one_price = []
    cvars_two_price = []
    expected_profits_one_price = []
    expected_profits_two_price = []
    bid_quantities_one_price = []
    bid_quantities_two_price = []
    runtime_start = time.time()
    for beta in betas:
        one_price_risk_averse = RiskAverseDayAheadQuantityBiddingModel(
            capacity=capacity,
            scenarios=in_sample_scenarios,
            weights=in_sample_weights,
            alpha=alpha,
            beta=beta,
            one_price_imbalance=True,
        )
        one_price_risk_averse.optimize()
        cvars_one_price.append(one_price_risk_averse.CVaR)
        expected_profits_one_price.append(one_price_risk_averse.expected_profit)
        bid_quantities_one_price.append(one_price_risk_averse.bid_quantities)

        two_price_risk_averse = RiskAverseDayAheadQuantityBiddingModel(
            capacity=capacity,
            scenarios=in_sample_scenarios,
            weights=in_sample_weights,
            alpha=alpha,
            beta=beta,
            one_price_imbalance=False,
        )
        two_price_risk_averse.optimize()
        cvars_two_price.append(two_price_risk_averse.CVaR)
        expected_profits_two_price.append(two_price_risk_averse.expected_profit)
        bid_quantities_two_price.append(two_price_risk_averse.bid_quantities)

    runtime_end = time.time()
    print(
        f"Runtime for Risk-Averse offering strategy: {runtime_end - runtime_start:.2f} seconds"
    )

    plt.figure(figsize=(12, 6))
    plt.plot(cvars_one_price, expected_profits_one_price, label="One-price", marker="o")
    plt.plot(cvars_two_price, expected_profits_two_price, label="Two-price", marker="s")
    plt.xlabel("CVaR [EUR]")
    plt.ylabel("Expected Profit [EUR]")
    plt.title("Risk-Averse Offering Strategy")
    plt.legend()
    plt.grid()
    plt.show()

    blue = iter(["#0000FF", "#0066FF", "#00AAFF"])
    red = iter(["#FF0000", "#FF6600", "#FFAA00"])
    plt.figure(figsize=(12, 6))
    for i, beta in enumerate(betas):
        if beta not in [0.0, 0.5, 1.0]:
            continue
        plt.plot(
            bid_quantities_one_price[i],
            label=f"One-price (beta={beta:.2f})",
            marker="o",
            color=next(blue),
        )
        plt.plot(
            bid_quantities_two_price[i],
            label=f"Two-price (beta={beta:.2f})",
            marker="s",
            color=next(red),
        )
    plt.xlabel("Hour")
    plt.ylabel("Bid Quantity [MWh]")
    plt.title("Risk-Averse Offering Strategy bid quantities")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
