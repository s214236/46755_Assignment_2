"""Main script for step 2 of assignment 2."""

import time

import matplotlib.pyplot as plt
import numpy as np

from assignment_2.step_2.bidding_model import (
    AlsoXFCRDUpModel,
    CVaRFCRDUpModel,
    FCRDUpModelBase,
)
from assignment_2.utils.data_loader import (
    load_in_sample_load,
    load_out_of_sample_load,
)


def evaluate_fixed_bid(
    bid: float, profiles: list[list[float]]
) -> tuple[float, float]:
    """Evaluate a fixed bid value against held-out profiles.

    Args:
        bid (float): Reserve bid in kW.
        profiles (list[list[float]]): Held-out load profiles.

    Returns:
        tuple[float, float]: The empirical violation rate and the average
        shortfall magnitude across all (minute, scenario) cells.
    """
    total_cells = 0
    violations = 0
    shortfall_sum = 0.0
    for profile in profiles:
        for load in profile:
            total_cells += 1
            if load < bid:
                violations += 1
                shortfall_sum += bid - load
    return violations / total_cells, shortfall_sum / total_cells


def main() -> None:
    """Main function to run the optimization model."""
    p_max = 600.0
    epsilon_p90 = 0.10

    # Load data
    in_sample_profiles: list[list[float]] = list(load_in_sample_load().values())
    out_of_sample_profiles: list[list[float]] = list(
        load_out_of_sample_load().values()
    )

    # Initialize and solve the optimization models
    runtime_start = time.time()
    cvar = CVaRFCRDUpModel(in_sample_profiles, epsilon=epsilon_p90, p_max=p_max)
    cvar.optimize()
    cvar_runtime = time.time() - runtime_start

    runtime_start = time.time()
    also_x = AlsoXFCRDUpModel(in_sample_profiles, epsilon=epsilon_p90, p_max=p_max)
    also_x.optimize()
    also_x_runtime = time.time() - runtime_start

    print(f"Runtime CVaR  : {cvar_runtime:.2f} seconds")
    print(f"Runtime ALSO-X: {also_x_runtime:.2f} seconds")

    print("\nIn-sample results:")
    print(f"  CVaR  : bid = {cvar.bid:7.3f} kW (VaR* = {cvar.VaR:7.3f} kW)")
    print(f"  ALSO-X: bid = {also_x.bid:7.3f} kW")

    # %% Out-of-sample verification
    print("\nOut-of-sample verification:")
    methods: list[tuple[str, FCRDUpModelBase]] = [
        ("CVaR  ", cvar),
        ("ALSO-X", also_x),
    ]
    for name, model in methods:
        v_rate, shortfall = model.evaluate(out_of_sample_profiles)
        p_rate = 1.0 - v_rate
        status = "P90 met" if v_rate <= epsilon_p90 else "P90 NOT met"
        print(
            f"  {name}: bid = {model.bid:7.3f} kW | "
            f"reliability = {p_rate * 100:6.2f} % | "
            f"E[shortfall] = {shortfall:7.4f} kW -> {status}"
        )

    # %% P-threshold sweep
    input("\nPress Enter to start P-threshold sweep...")
    print("\nStarting P-threshold sweep (ALSO-X)...")

    p_thresholds = np.linspace(0.80, 1.00, 21)
    epsilons = 1.0 - p_thresholds

    bids: list[float] = []
    expected_shortfalls: list[float] = []
    runtime_start = time.time()
    for eps in epsilons:
        model = AlsoXFCRDUpModel(
            in_sample_profiles, epsilon=max(eps, 0.0), p_max=p_max
        )
        model.optimize()
        bids.append(model.bid)
        _, shortfall = evaluate_fixed_bid(model.bid, out_of_sample_profiles)
        expected_shortfalls.append(shortfall)
    print(f"Runtime for P-threshold sweep: {time.time() - runtime_start:.2f} seconds")

    p_pct = p_thresholds * 100.0

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].plot(p_pct, bids, marker="o")
    axes[0].set_xlabel("P-threshold [%]")
    axes[0].set_ylabel("In-sample optimal bid [kW]")
    axes[0].set_title("In-sample reserve bid vs P-threshold (ALSO-X)")
    axes[0].grid(True)

    axes[1].plot(p_pct, expected_shortfalls, marker="s", color="tab:red")
    axes[1].set_xlabel("P-threshold [%]")
    axes[1].set_ylabel("Out-of-sample expected shortfall [kW]")
    axes[1].set_title("Out-of-sample expected shortfall vs P-threshold")
    axes[1].grid(True)

    fig.tight_layout()
    plt.show()

    print("\nSummary (P-threshold | bid kW | E[shortfall] kW):")
    for p, b, s in zip(p_pct, bids, expected_shortfalls, strict=True):
        print(f"  {p:6.2f} %  |  {b:7.3f}  |  {s:7.4f}")


if __name__ == "__main__":
    main()
