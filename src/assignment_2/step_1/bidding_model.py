"""Optimization model for quantity-based bidding in the day-ahead market."""

from gurobipy import GRB, Model, quicksum


class DayAheadQuantityBiddingModel:
    """Optimization model for quantity-based bidding in the day-ahead market."""

    def __init__(
        self, scenarios: list[dict[str, float | dict[str, list[float]]]]
    ) -> None:
        """Initialize the model."""
