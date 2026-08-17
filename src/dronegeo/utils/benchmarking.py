"""
dronegeo.utils.benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Execution timers and performance profiling utilities.
"""

from __future__ import annotations
import time
import functools
from typing import Callable, Any, Optional


class ExecutionTimer:
    """
    Context manager to accurately measure wall-clock execution time of operations.

    Real-World Applications:
        - Benchmarking: Measuring throughput (points/sec) across different CPU worker counts.

    Example:
        >>> from dronegeo.utils import ExecutionTimer
        >>> with ExecutionTimer("DTM Generation") as timer:
        ...     dtm = dg.dem.create_dtm("survey.laz", "dtm.tif")
        >>> print(f"Elapsed: {timer.elapsed_seconds:.2f}s")
    """

    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_seconds: float = 0.0

    def __enter__(self) -> ExecutionTimer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed_seconds = self.end_time - self.start_time


def time_operation(fn: Callable) -> Callable:
    """
    Decorator that prints execution time of the decorated function.

    Example:
        >>> from dronegeo.utils import time_operation
        >>> @time_operation
        ... def my_heavy_task():
        ...     pass
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> Any:
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - t0
        print(f"[Timer] {fn.__name__} completed in {elapsed:.3f}s")
        return result
    return wrapper
