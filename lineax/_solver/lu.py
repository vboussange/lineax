from typing import Any
from typing_extensions import TypeAlias

import jax.scipy as jsp
from jaxtyping import Array, PyTree

from .._operator import AbstractLinearOperator
from .._solution import RESULTS
from .._solve import AbstractLinearSolver
from .misc import (
    pack_structures,
    PackedStructures,
    ravel_vector,
    transpose_packed_structures,
    unravel_solution,
)


_LUState: TypeAlias = tuple[tuple[Array, Array], PackedStructures, bool]


class LU(AbstractLinearSolver[_LUState]):
    """LU solver for linear systems.

    This solver can only handle square nonsingular operators.
    """

    def init(self, operator: AbstractLinearOperator, options: dict[str, Any]):
        del options
        if operator.in_size() != operator.out_size():
            raise ValueError(
                "`LU` may only be used for linear solves with square matrices"
            )
        packed_structures = pack_structures(operator)
        return jsp.linalg.lu_factor(operator.as_matrix()), packed_structures, False

    def compute(
        self, state: _LUState, vector: PyTree[Array], options: dict[str, Any]
    ) -> tuple[PyTree[Array], RESULTS, dict[str, Any]]:
        del options
        lu_and_piv, packed_structures, transpose = state
        trans = 1 if transpose else 0
        vector = ravel_vector(vector, packed_structures)
        solution = jsp.linalg.lu_solve(lu_and_piv, vector, trans=trans)
        solution = unravel_solution(solution, packed_structures)
        return solution, RESULTS.successful, {}  # pyright: ignore

    def transpose(
        self,
        state: _LUState,
        options: dict[str, Any],
    ):
        lu_and_piv, packed_structures, transpose = state
        transposed_packed_structures = transpose_packed_structures(packed_structures)
        transpose_state = lu_and_piv, transposed_packed_structures, not transpose
        transpose_options = {}
        return transpose_state, transpose_options

    def allow_dependent_columns(self, operator):
        return False

    def allow_dependent_rows(self, operator):
        return False