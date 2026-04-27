"""Optimization model for quantity-based bidding in the day-ahead market."""

from typing import Any

from gurobipy import GRB, Constr, Model, Var, quicksum, tupledict


class DayAheadQuantityBiddingModel:
    """Optimization model for quantity-based bidding in the day-ahead market."""

    def __init__(
        self,
        capacity: float,
        scenarios: list[dict[str, list[float]]],
        weights: list[float],
        one_price_imbalance: bool = True,
    ) -> None:
        """Initialize the model.

        Validates that each scenario contains a `data` dictionary with exactly
        `da_prices`, `system_imbalance`, and `wind_power`, where each value is
        a list of 24 floats, and that `weight` is a float.

        Args:
            capacity (float): Maximum quantity that can be bid in each hour.
            scenarios (list[dict[str, list[float]]]): List of scenarios.
            weights (list[float]): List of weights for each scenario.
            one_price_imbalance (bool): Whether to use a single price for imbalance penalties.

        """
        self.scenarios = scenarios
        self.num_scenarios = len(scenarios)
        total_weight = sum(weights)
        self.weights = [weight / total_weight for weight in weights]
        self.capacity = capacity
        self.one_price_imbalance = one_price_imbalance
        self.create_model()

    def create_model(self) -> None:
        """Create the optimization model."""
        self.model = Model("DayAheadQuantityBidding")
        self.vars: dict[str, tupledict[Any, Var]] = {}
        self.var: dict[str, Var] = {}
        self.constr: dict[str, Constr] = {}

        # Variables
        self.vars["bid_quantity"] = self.model.addVars(
            24, lb=0.0, ub=self.capacity, name="bid_quantity"
        )

        self.vars["imbalance"] = self.model.addVars(
            24, self.num_scenarios, lb=-GRB.INFINITY, ub=GRB.INFINITY, name="imbalance"
        )

        self.vars["imbalance_positive"] = self.model.addVars(
            24, self.num_scenarios, lb=0.0, ub=self.capacity, name="imbalance_positive"
        )
        self.vars["imbalance_negative"] = self.model.addVars(
            24, self.num_scenarios, lb=0.0, ub=self.capacity, name="imbalance_negative"
        )

        # Objective
        self.model.setObjective(
            quicksum(
                self.weights[scenario_index]
                * quicksum(
                    self.vars["bid_quantity"][hour] * scenario["da_prices"][hour]
                    + self.vars["imbalance_positive"][hour, scenario_index]
                    * scenario["da_prices"][hour]
                    * (
                        (1.25 if self.one_price_imbalance else 1.0)
                        if (scenario["system_imbalance"][hour] > 0.5)
                        else 0.85
                    )
                    - self.vars["imbalance_negative"][hour, scenario_index]
                    * scenario["da_prices"][hour]
                    * (
                        (0.85 if self.one_price_imbalance else 1.0)
                        if (scenario["system_imbalance"][hour] <= 0.5)
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
                        == scenario["wind_power"][hour]
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
        self.bid_quantities = [
            round(self.vars["bid_quantity"][hour].X, 2) for hour in range(24)
        ]
        self.expected_profit = self.model.objVal

        self.scenarios_profit = []
        for _, scenario in enumerate(self.scenarios):
            imbalance_positive = [
                max(0, scenario["wind_power"][hour] - self.vars["bid_quantity"][hour].X)
                for hour in range(24)
            ]
            imbalance_negative = [
                max(0, self.vars["bid_quantity"][hour].X - scenario["wind_power"][hour])
                for hour in range(24)
            ]
            profit = sum(
                self.vars["bid_quantity"][hour].X * scenario["da_prices"][hour]
                + imbalance_positive[hour]
                * scenario["da_prices"][hour]
                * (
                    (1.25 if self.one_price_imbalance else 1.0)
                    if (scenario["system_imbalance"][hour] > 0.5)
                    else 0.85
                )
                - imbalance_negative[hour]
                * scenario["da_prices"][hour]
                * (
                    (0.85 if self.one_price_imbalance else 1.0)
                    if (scenario["system_imbalance"][hour] <= 0.5)
                    else 1.25
                )
                for hour in range(24)
            )
            self.scenarios_profit.append(profit)

    def out_of_sample_profit(
        self, out_of_sample_scenarios: list[dict[str, list[float]]]
    ) -> float:
        """Calculate the expected profit for out-of-sample scenarios.

        Args:
            out_of_sample_scenarios (list[dict[str, list[float]]]): List of out-of-sample scenarios.

        Returns:
            float: The expected profit for the out-of-sample scenarios.
        """
        if not hasattr(self, "bid_quantities"):
            raise ValueError(
                "Model must be optimized before calculating out-of-sample profit."
            )

        total_profit = 0.0
        for _, scenario in enumerate(out_of_sample_scenarios):
            imbalance_positive = [
                max(0, scenario["wind_power"][hour] - self.vars["bid_quantity"][hour].X)
                for hour in range(24)
            ]
            imbalance_negative = [
                max(0, self.vars["bid_quantity"][hour].X - scenario["wind_power"][hour])
                for hour in range(24)
            ]
            profit = sum(
                self.vars["bid_quantity"][hour].X * scenario["da_prices"][hour]
                + imbalance_positive[hour]
                * scenario["da_prices"][hour]
                * (
                    (1.25 if self.one_price_imbalance else 1.0)
                    if (scenario["system_imbalance"][hour] > 0.5)
                    else 0.85
                )
                - imbalance_negative[hour]
                * scenario["da_prices"][hour]
                * (
                    (0.85 if self.one_price_imbalance else 1.0)
                    if (scenario["system_imbalance"][hour] <= 0.5)
                    else 1.25
                )
                for hour in range(24)
            )
            total_profit += profit
        return total_profit / len(out_of_sample_scenarios)


class RiskAverseDayAheadQuantityBiddingModel(DayAheadQuantityBiddingModel):
    """Optimization model for risk-averse quantity-based bidding in the day-ahead market."""

    def __init__(
        self,
        capacity: float,
        scenarios: list[dict[str, list[float]]],
        weights: list[float],
        alpha: float = 0.95,
        beta: float = 1,
        one_price_imbalance: bool = True,
    ) -> None:
        """Initialize the risk-averse model.

        Args:
            capacity (float): Maximum quantity that can be bid in each hour.
            scenarios (list[dict[str, list[float]]]): List of scenarios.
            weights (list[float]): List of weights for each scenario.
            alpha (float): Confidence level for CVaR calculation.
            beta (float): Risk aversion parameter. 1 means only the CVaR is considered, while 0 means only the expected profit is considered.
            one_price_imbalance (bool): Whether to use a single price for imbalance penalties.

        """
        self.alpha = alpha
        self.beta = beta
        super().__init__(capacity, scenarios, weights, one_price_imbalance)

    def create_model(self) -> None:
        """Create the optimization model."""
        super().create_model()

        # Additional variables for CVaR calculation
        self.var["VaR"] = self.model.addVar(
            lb=-GRB.INFINITY, ub=GRB.INFINITY, name="VaR"
        )
        self.vars["eta"] = self.model.addVars(
            self.num_scenarios, lb=0.0, ub=GRB.INFINITY, name="eta"
        )

        # Modify objective to include CVaR
        self.model.setObjective(
            (1 - self.beta)
            * quicksum(
                self.weights[scenario_index]
                * quicksum(
                    self.vars["bid_quantity"][hour] * scenario["da_prices"][hour]
                    + self.vars["imbalance_positive"][hour, scenario_index]
                    * scenario["da_prices"][hour]
                    * (
                        (1.25 if self.one_price_imbalance else 1.0)
                        if (scenario["system_imbalance"][hour] > 0.5)
                        else 0.85
                    )
                    - self.vars["imbalance_negative"][hour, scenario_index]
                    * scenario["da_prices"][hour]
                    * (
                        (0.85 if self.one_price_imbalance else 1.0)
                        if (scenario["system_imbalance"][hour] <= 0.5)
                        else 1.25
                    )
                    for hour in range(24)
                )
                for scenario_index, scenario in enumerate(self.scenarios)
            )
            + self.beta
            * (
                self.var["VaR"]
                - (1 / (1 - self.alpha))
                * quicksum(
                    self.weights[scenario_index] * self.vars["eta"][scenario_index]
                    for scenario_index in range(self.num_scenarios)
                )
            ),
            GRB.MAXIMIZE,
        )

        # Constraints for CVaR calculation
        for scenario_index, scenario in enumerate(self.scenarios):
            profit = quicksum(
                self.vars["bid_quantity"][hour] * scenario["da_prices"][hour]
                + self.vars["imbalance_positive"][hour, scenario_index]
                * scenario["da_prices"][hour]
                * (
                    (1.25 if self.one_price_imbalance else 1.0)
                    if (scenario["system_imbalance"][hour] > 0.5)
                    else 0.85
                )
                - self.vars["imbalance_negative"][hour, scenario_index]
                * scenario["da_prices"][hour]
                * (
                    (0.85 if self.one_price_imbalance else 1.0)
                    if (scenario["system_imbalance"][hour] <= 0.5)
                    else 1.25
                )
                for hour in range(24)
            )
            self.model.addLConstr(
                self.vars["eta"][scenario_index] >= self.var["VaR"] - profit,
                name=f"cvar_constraint_{scenario_index}",
            )

    def optimize(self) -> None:
        """Optimize the model."""
        super().optimize()
        self.VaR = self.var["VaR"].X
        self.CVaR = self.VaR - (1 / (1 - self.alpha)) * sum(
            self.weights[scenario_index] * self.vars["eta"][scenario_index].X
            for scenario_index in range(self.num_scenarios)
        )

        self.expected_profit = sum(
            self.weights[s] * self.scenarios_profit[s]
            for s in range(self.num_scenarios)
        )
