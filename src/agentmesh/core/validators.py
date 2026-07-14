"""Built-in output validators.

A validator is `Callable[[str], str | None]`: given a task's raw output, it
returns a human-readable failure reason, or `None` if the output is fine.
Attach one to `Task.validate` to catch outputs that return successfully from
the provider but are still garbage -- something a bare try/except around the
provider call can never see, because nothing raised.
"""

from __future__ import annotations

from collections.abc import Callable

Validator = Callable[[str], "str | None"]


def non_empty(min_length: int = 1) -> Validator:
    """Fail if the output is shorter than `min_length` non-whitespace characters."""

    def _validate(output: str) -> str | None:
        if len(output.strip()) < min_length:
            return f"output has fewer than {min_length} non-whitespace characters"
        return None

    return _validate


def not_contains(*markers: str) -> Validator:
    """Fail if any of `markers` appears in the output (case-insensitive)."""

    def _validate(output: str) -> str | None:
        lowered = output.lower()
        for marker in markers:
            if marker.lower() in lowered:
                return f"output contains disallowed marker '{marker}'"
        return None

    return _validate


def all_of(*validators: Validator) -> Validator:
    """Combine validators; fails on the first one that fails."""

    def _validate(output: str) -> str | None:
        for validator in validators:
            reason = validator(output)
            if reason is not None:
                return reason
        return None

    return _validate
