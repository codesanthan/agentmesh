"""Execution strategies: how the orchestrator walks the task graph."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Callable


class Strategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SUPERVISOR = "supervisor"


def run_wave_sequential(wave: list[str], run_one: Callable[[str], None]) -> None:
    for task_id in wave:
        run_one(task_id)


def run_wave_parallel(
    wave: list[str], run_one: Callable[[str], None], max_workers: int = 8
) -> None:
    if len(wave) == 1:
        run_one(wave[0])
        return
    with ThreadPoolExecutor(max_workers=min(max_workers, len(wave))) as pool:
        futures = [pool.submit(run_one, task_id) for task_id in wave]
        for future in futures:
            future.result()
