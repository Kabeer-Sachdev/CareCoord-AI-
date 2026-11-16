from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class ConstraintCheckResult:
    is_valid: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.is_valid or self.violations:
            return "FAILED"
        if self.warnings:
            return "WARNING"
        return "PASSED"

class BaseOptimizer(ABC):
    """Abstract base class for resource optimization modules."""

    @abstractmethod
    def optimize(self, **kwargs) -> Dict[str, Any]:
        """Executes optimization algorithm and returns structured results."""
        pass

    @abstractmethod
    def validate_constraints(self, allocations: List[Dict[str, Any]], **kwargs) -> ConstraintCheckResult:
        """Post-solve verification checking all operational constraints."""
        pass
