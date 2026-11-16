from typing import Tuple, Optional
from ortools.linear_solver import pywraplp

class SolverFactory:
    """
    Factory for Google OR-Tools solvers:
    - Mixed Integer Linear Programming (MIP) via SCIP / CBC: for discrete combinatorial allocation,
      shift scheduling, and non-overlapping constraint problems.
    - Linear Programming (LP) via GLOP: for continuous resource distribution.
    """

    @staticmethod
    def create_mip_solver(preferred_id: str = "SCIP", max_time_seconds: float = 10.0) -> pywraplp.Solver:
        """
        Creates an OR-Tools Mixed-Integer Programming solver instance.
        Tries SCIP first, falls back to CBC if needed.
        """
        solver = pywraplp.Solver.CreateSolver(preferred_id)
        if not solver and preferred_id != "CBC":
            solver = pywraplp.Solver.CreateSolver("CBC")
        if not solver:
            raise RuntimeError(f"Failed to initialize Google OR-Tools MIP solver ({preferred_id}/CBC).")

        solver.SetTimeLimit(int(max_time_seconds * 1000))
        return solver

    @staticmethod
    def create_linear_solver(solver_id: str = "GLOP", max_time_seconds: float = 10.0) -> pywraplp.Solver:
        """Creates a Google OR-Tools continuous LP solver (GLOP)."""
        solver = pywraplp.Solver.CreateSolver(solver_id)
        if not solver:
            raise RuntimeError(f"Failed to initialize Google OR-Tools LP solver ({solver_id}).")
        solver.SetTimeLimit(int(max_time_seconds * 1000))
        return solver

    @staticmethod
    def parse_solver_status(status_code: int) -> str:
        """Translates OR-Tools integer status codes to standardized string representations."""
        if status_code == pywraplp.Solver.OPTIMAL:
            return "OPTIMAL"
        elif status_code == pywraplp.Solver.FEASIBLE:
            return "FEASIBLE"
        elif status_code == pywraplp.Solver.INFEASIBLE:
            return "INFEASIBLE"
        elif status_code == pywraplp.Solver.UNBOUNDED:
            return "UNBOUNDED"
        elif status_code == pywraplp.Solver.ABNORMAL:
            return "FAILED"
        else:
            return "UNKNOWN"
