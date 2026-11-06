"""Immutable configuration snapshots created at CLI boundaries."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class PipelineConfig:
    """Attribute-readable, picklable snapshot replacing internal Namespace use.

    This is a *shallow* snapshot: the top-level mapping is read-only, but
    nested lists or dictionaries are the original objects and stay mutable.
    """

    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    @classmethod
    def from_namespace(cls, namespace: Any) -> "PipelineConfig":
        return cls(vars(namespace))

    def __getattr__(self, name: str) -> Any:
        try:
            return self.values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)

    def __reduce__(self):
        return (type(self), (dict(self.values),))
