from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class P1Run:
    edition: str
    commentary: int | None
    grid: tuple[int, int]
    rows: int


RUNS = (
    P1Run("qcmr:2021-09-30:none", None, (35, 36), 58),
    P1Run("qcmr:2021-12-31:none", None, (34, 35), 58),
    P1Run("qcmr:2022-03-31:none", None, (35, 36), 56),
    P1Run("qcmr:2022-06-30:none", 34, (35, 36), 56),
    P1Run("qcmr:2022-09-30:none", 34, (35, 36), 58),
    P1Run("qcmr:2022-12-31:none", 34, (35, 36), 58),
    P1Run("qcmr:2023-03-31:none", 33, (34, 35), 58),
    P1Run("qcmr:2023-06-30:none", 31, (32, 33), 58),
    P1Run("qcmr:2023-09-30:none", 32, (33, 34), 57),
    P1Run("qcmr:2023-12-31:none", None, (32, 33), 57),
    P1Run("qcmr:2024-03-31:none", 31, (32, 33), 57),
    P1Run("qcmr:2024-06-30:none", 31, (32, 33), 59),
    P1Run("qcmr:2024-09-30:none", 32, (33, 34), 58),
    P1Run("qcmr:2024-12-31:none", 33, (34, 35), 58),
    P1Run("qcmr:2025-03-31:none", 32, (33, 34), 58),
    P1Run("qcmr:2025-06-30:none", 30, (31, 32), 58),
    P1Run("qcmr:2025-09-30:none", 34, (35, 36), 63),
    P1Run("qcmr:2025-12-31:none", 35, (36, 37), 63),
    P1Run("qcmr:2026-03-31:none", 35, (36, 37), 63),
    P1Run("qcmr:2026-06-30:none", 32, (33, 34), 63),
)
