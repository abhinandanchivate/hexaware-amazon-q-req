"""Utility helpers for generating dynamic sample responses.

These helpers keep the illustrative payloads aligned with the API
specification while avoiding brittle hard-coded identifiers or timestamps.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, MutableMapping
from uuid import uuid4

from django.utils import timezone


def isoformat_now() -> str:
    """Return the current timestamp in ISO 8601 format with UTC suffix."""

    value = timezone.now().isoformat()
    return value.replace("+00:00", "Z") if value.endswith("+00:00") else value


def generate_identifier(prefix: str, *, override: str | None = None) -> str:
    """Create a deterministic looking identifier for sample responses."""

    return override or f"{prefix}-{uuid4()}"


def deep_merge(base: Mapping[str, Any], overrides: Mapping[str, Any] | None) -> dict[str, Any]:
    """Recursively merge mapping values.

    ``overrides`` wins over ``base`` and nested dictionaries are merged to allow
    callers to provide partial payloads while keeping sample defaults.
    """

    result: dict[str, Any] = deepcopy(base)
    if not overrides:
        return result

    for key, value in overrides.items():
        if (
            isinstance(value, Mapping)
            and key in result
            and isinstance(result[key], MutableMapping)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def ensure_list(value: Any, default: list[Any]) -> list[Any]:
    """Return ``value`` if it is a non-empty list, otherwise ``default``."""

    if isinstance(value, list) and value:
        return value
    return deepcopy(default)
