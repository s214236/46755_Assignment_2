"""Optimization models for FCR-D UP reserve bidding under the P90 requirement."""

from typing import Any

from gurobipy import GRB, Constr, Model, Var, quicksum, tupledict


class FCRDUpModelBase:
    """Common helpers shared by both FCR-D UP models."""

    bid: float

    def __init__(
        self,
        profiles: list[list[float]],
        epsilon: float = 0.10,
        p_max: float = 600.0,
    ) -> None:
        """Initialize the model.

        Args:
            profiles (list[list[float]]): In-sample load profiles. Outer list
                indexes scenarios, inner list indexes minutes.
            epsilon (float): Allowed shortfall probability (1 - P-threshold).
            p_max (float): Upper bound on the reserve bid in kW.

        """
        n_minutes = len(profiles[0])
        self.profiles = profiles
        self.n_scenarios = len(profiles)
        self.n_minutes = n_minutes
        self.epsilon = epsilon
        self.p_max = p_max

    def evaluate(self, profiles: list[list[float]]) -> tuple[float, float]:
        """Evaluate the optimized bid against held-out profiles.

        Args:
            profiles (list[list[float]]): Held-out load profiles.

        Returns:
            tuple[float, float]: The empirical violation rate and the average
            shortfall magnitude across all (minute, scenario) cells.
        """
        if not hasattr(self, "bid"):
            raise ValueError("Model must be optimized before evaluation.")
        bid = self.bid
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


class CVaRFCRDUpModel(FCRDUpModelBase):
    """CVaR-reformulated P90 reserve-bidding LP for FCR-D UP."""

    def __init__(
        self,
        profiles: list[list[float]],
        epsilon: float = 0.10,
        p_max: float = 600.0,
    ) -> None:
        """Initialize the CVaR model.

        Args:
            profiles (list[list[float]]): In-sample load profiles.
            epsilon (float): Allowed shortfall probability (1 - P-threshold).
            p_max (float): Upper bound on the reserve bid in kW.

        """
        super().__init__(profiles, epsilon, p_max)
        self.create_model()

    def create_model(self) -> None:
        """Create the optimization model."""
        self.model = Model("CVaR_FCRD_Up")
        self.model.Params.OutputFlag = 0
        self.vars: dict[str, tupledict[Any, Var]] = {}
        self.var: dict[str, Var] = {}
        self.constr: dict[str, Constr] = {}

        # Variables
        self.var["bid"] = self.model.addVar(lb=0.0, ub=self.p_max, name="bid")
        self.var["VaR"] = self.model.addVar(
            lb=-GRB.INFINITY, ub=GRB.INFINITY, name="VaR"
        )
        self.vars["eta"] = self.model.addVars(
            self.n_minutes, self.n_scenarios, lb=0.0, name="eta"
        )

        # Objective
        self.model.setObjective(self.var["bid"], GRB.MAXIMIZE)

        # Constraints
        budget_factor = 1.0 / (self.epsilon * self.n_minutes * self.n_scenarios)
        self.constr["cvar_budget"] = self.model.addLConstr(
            self.var["VaR"]
            + budget_factor
            * quicksum(
                self.vars["eta"][m, w]
                for m in range(self.n_minutes)
                for w in range(self.n_scenarios)
            )
            <= 0,
            name="cvar_budget",
        )

        for m in range(self.n_minutes):
            for w in range(self.n_scenarios):
                self.constr[f"eta_{m}_{w}"] = self.model.addLConstr(
                    self.vars["eta"][m, w]
                    >= self.var["bid"] - self.profiles[w][m] - self.var["VaR"],
                    name=f"eta_{m}_{w}",
                )

        self.model.update()

    def optimize(self) -> None:
        """Optimize the model."""
        self.model.optimize()
        self.bid = self.var["bid"].X
        self.VaR = self.var["VaR"].X


class AlsoXFCRDUpModel(FCRDUpModelBase):
    """ALSO-X iterative LP algorithm for the P90 reserve bid."""

    big_m: float = 1.0e4
    tol: float = 1.0e-3
    max_iter: int = 60

    def _solve_lp_relaxation(self) -> float:
        """Solve the LP relaxation of the MILP for an upper bound on the bid.

        Returns:
            float: Upper bound on the chance-constrained optimum.
        """
        model = Model("ALSO-X_LP_relaxation")
        model.Params.OutputFlag = 0

        bid = model.addVar(lb=0.0, ub=self.p_max, name="bid")
        y = model.addVars(self.n_minutes, self.n_scenarios, lb=0.0, ub=1.0, name="y")

        for m in range(self.n_minutes):
            for w in range(self.n_scenarios):
                model.addLConstr(
                    bid - self.profiles[w][m] <= self.big_m * y[m, w],
                    name=f"bigm_{m}_{w}",
                )
        model.addLConstr(
            quicksum(
                y[m, w] for m in range(self.n_minutes) for w in range(self.n_scenarios)
            )
            <= self.epsilon * self.n_minutes * self.n_scenarios,
            name="budget",
        )

        model.setObjective(bid, GRB.MAXIMIZE)
        model.optimize()
        return float(bid.X)

    def _solve_subproblem(self, q_mid: float) -> int:
        """Solve the ALSO-X feasibility sub-LP at level q_mid.

        Args:
            q_mid (float): Trial bid level in kW.

        Returns:
            int: The number of (minute, scenario) cells with strictly positive
            violation slack.
        """
        model = Model("ALSO-X_subproblem")
        model.Params.OutputFlag = 0

        v = model.addVars(self.n_minutes, self.n_scenarios, lb=0.0, name="v")
        for m in range(self.n_minutes):
            for w in range(self.n_scenarios):
                model.addLConstr(
                    v[m, w] >= q_mid - self.profiles[w][m],
                    name=f"slack_{m}_{w}",
                )

        model.setObjective(
            quicksum(
                v[m, w] for m in range(self.n_minutes) for w in range(self.n_scenarios)
            ),
            GRB.MINIMIZE,
        )
        model.optimize()

        slack_tol = 1.0e-6
        return sum(
            1
            for m in range(self.n_minutes)
            for w in range(self.n_scenarios)
            if slack_tol < v[m, w].X
        )

    def optimize(self) -> None:
        """Run the ALSO-X bisection and store the resulting bid."""
        budget = self.epsilon * self.n_minutes * self.n_scenarios

        lp_upper = self._solve_lp_relaxation()
        self.lp_upper_bound = lp_upper

        q_lo = 0.0
        q_hi = lp_upper
        best = 0.0

        for iteration in range(1, self.max_iter + 1):
            if q_hi - q_lo <= self.tol:
                break
            q_mid = 0.5 * (q_lo + q_hi)
            violations = self._solve_subproblem(q_mid)
            if violations <= budget:
                q_lo = q_mid
                best = q_mid
            else:
                q_hi = q_mid

        self.bid = best
        self.n_iterations = iteration
