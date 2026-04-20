"""Optimization model for quantity-based bidding in the day-ahead market."""

from typing import Any

from gurobipy import GRB, Constr, Model, Var, quicksum, tupledict


class DayAheadQuantityBiddingModel:
    """Optimization model for quantity-based bidding in the day-ahead market."""

    REQUIRED_DATA_KEYS = {"da_prices", "system_imbalance", "wind_power"}

    def __init__(
        self,
        capacity: float,
        scenarios: list[dict[str, float | dict[str, list[float]]]],
        one_price_imbalance: bool = True,
    ) -> None:
        """Initialize the model.

        Validates that each scenario contains a `data` dictionary with exactly
        `da_prices`, `system_imbalance`, and `wind_power`, where each value is
        a list of 24 floats, and that `weight` is a float.

        Args:
            capacity (float): Maximum quantity that can be bid in each hour.
            scenarios (list[dict[str, float | dict[str, list[float]]]]): List of scenarios, where each scenario is a dictionary with
                'data' and 'weight' keys.
            one_price_imbalance (bool): Whether to use a single price for imbalance penalties.

        """
        self._validate_scenarios(scenarios)
        self.scenarios = scenarios
        self.num_scenarios = len(scenarios)
        total_weight = sum(scenario["weight"] for scenario in scenarios)
        self.weights = [scenario["weight"] / total_weight for scenario in scenarios]
        self.capacity = capacity
        self.one_price_imbalance = one_price_imbalance
        self.create_model()

    def create_model(self) -> None:
        """Create the optimization model."""
        self.model = Model("DayAheadQuantityBidding")
        self.vars: dict[str, tupledict[Any, Var]] = {}
        self.constr: dict[str, Constr] = {}

        # Variables
        self.vars["bid_quantity"] = self.model.addVars(
            24, lb=0.0, ub=self.capacity, name="bid_quantity"
        )

        self.vars["imbalance"] = self.model.addVars(
            24, self.num_scenarios, lb=-GRB.INFINITY, ub=GRB.INFINITY, name="imbalance"
        )

        self.vars["imbalance_positive"] = self.model.addVars(
            24, self.num_scenarios, lb=0.0, ub=GRB.INFINITY, name="imbalance_positive"
        )
        self.vars["imbalance_negative"] = self.model.addVars(
            24, self.num_scenarios, lb=0.0, ub=GRB.INFINITY, name="imbalance_negative"
        )

        # Objective
        self.model.setObjective(
            quicksum(
                self.weights[scenario_index]
                * quicksum(
                    self.vars["bid_quantity"][hour]
                    * scenario["data"]["da_prices"][hour]
                    + self.vars["imbalance_positive"][hour, scenario_index]
                    * scenario["data"]["da_prices"][hour]
                    * (
                        (1.25 if self.one_price_imbalance else 1.0)
                        if (scenario["data"]["system_imbalance"][hour] == 1.0)
                        else 0.85
                    )
                    - self.vars["imbalance_negative"][hour, scenario_index]
                    * scenario["data"]["da_prices"][hour]
                    * (
                        (0.85 if self.one_price_imbalance else 1.0)
                        if (scenario["data"]["system_imbalance"][hour] == 0.0)
                        else 1.25
                    )
                    for hour in range(24)
                )
                for scenario_index, scenario in enumerate(self.scenarios)
            ),
            GRB.MAXIMIZE,
        )

        # Constraints
        for hour in range(24):
            for scenario_index, scenario in enumerate(self.scenarios):
                self.constr[f"imbalance_real_{hour}_{scenario_index}"] = (
                    self.model.addLConstr(
                        self.vars["imbalance"][hour, scenario_index]
                        == scenario["data"]["wind_power"][hour]
                        - self.vars["bid_quantity"][hour],
                        name=f"imbalance_real_{hour}_{scenario_index}",
                    )
                )
                self.constr[f"imbalance_result_{hour}_{scenario_index}"] = (
                    self.model.addLConstr(
                        self.vars["imbalance"][hour, scenario_index]
                        == self.vars["imbalance_positive"][hour, scenario_index]
                        - self.vars["imbalance_negative"][hour, scenario_index],
                        name=f"imbalance_result_{hour}_{scenario_index}",
                    )
                )

                self.constr[f"imbalance_positive_{hour}_{scenario_index}"] = (
                    self.model.addLConstr(
                        self.vars["imbalance_positive"][hour, scenario_index]
                        >= self.vars["imbalance"][hour, scenario_index],
                        name=f"imbalance_positive_{hour}_{scenario_index}",
                    )
                )
                self.constr[f"imbalance_negative_{hour}_{scenario_index}"] = (
                    self.model.addLConstr(
                        self.vars["imbalance_negative"][hour, scenario_index]
                        >= -self.vars["imbalance"][hour, scenario_index],
                        name=f"imbalance_negative_{hour}_{scenario_index}",
                    )
                )

        self.model.update()

    def optimize(self) -> None:
        """Optimize the model."""
        self.model.optimize()
        self.bid_quantities = [self.vars["bid_quantity"][hour].X for hour in range(24)]

    @classmethod
    def _validate_scenarios(
        cls, scenarios: list[dict[str, float | dict[str, list[float]]]]
    ) -> None:
        if not isinstance(scenarios, list):
            raise TypeError("scenarios must be a list")

        for scenario_index, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict):
                raise TypeError(
                    f"Scenario at index {scenario_index} must be a dictionary"
                )

            scenario_weight = scenario.get("weight")
            if not isinstance(scenario_weight, float):
                raise TypeError(
                    f"Scenario at index {scenario_index} must contain a 'weight' of type float"
                )

            scenario_data = scenario.get("data")
            if not isinstance(scenario_data, dict):
                raise TypeError(
                    f"Scenario at index {scenario_index} must contain a 'data' dictionary"
                )

            present_keys = set(scenario_data.keys())
            if present_keys != cls.REQUIRED_DATA_KEYS:
                missing_keys = sorted(cls.REQUIRED_DATA_KEYS - present_keys)
                extra_keys = sorted(present_keys - cls.REQUIRED_DATA_KEYS)
                details: list[str] = []

                if missing_keys:
                    details.append(f"missing keys: {missing_keys}")
                if extra_keys:
                    details.append(f"extra keys: {extra_keys}")

                raise ValueError(
                    "Scenario at index "
                    f"{scenario_index} has invalid data keys ({'; '.join(details)})"
                )

            for key in cls.REQUIRED_DATA_KEYS:
                values = scenario_data[key]
                if not isinstance(values, list):
                    raise TypeError(
                        f"Scenario at index {scenario_index} key '{key}' must be a list"
                    )

                if len(values) != 24:
                    raise ValueError(
                        f"Scenario at index {scenario_index} key '{key}' must have exactly 24 values"
                    )

                non_float_indices = [
                    value_index
                    for value_index, value in enumerate(values)
                    if not isinstance(value, float)
                ]
                if non_float_indices:
                    raise TypeError(
                        f"Scenario at index {scenario_index} key '{key}' contains non-float values "
                        f"at indices {non_float_indices}"
                    )
