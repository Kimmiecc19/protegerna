"""The six public stages of the proteogenomic database workflow."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowStage:
    number: int
    name: str
    implementations: tuple[str, ...]

    @property
    def slug(self) -> str:
        return self.name.lower().replace(" ", "_")


WORKFLOW_STAGES = (
    WorkflowStage(1, "Validate reference annotation", ("validate",)),
    WorkflowStage(2, "Reconstruct proteins", ("rmats", "suppa", "fusion")),
    # Merge and DIA filtering are separate biological decisions implemented by
    # one streaming command so proteins need not be serialized twice.
    WorkflowStage(3, "Merge proteins", ("merge",)),
    WorkflowStage(4, "Filter for DIA suitability", ("merge",)),
    WorkflowStage(5, "Validate database", ("benchmark", "qc")),
    WorkflowStage(6, "Generate release", ("report",)),
)

STAGES_BY_SLUG = {stage.slug: stage for stage in WORKFLOW_STAGES}


def implementations_for(stage_slugs: list[str]) -> list[str]:
    """Expand public stages to internal commands without running duplicates."""
    selected: list[str] = []
    for slug in stage_slugs:
        for implementation in STAGES_BY_SLUG[slug].implementations:
            if implementation not in selected:
                selected.append(implementation)
    return selected


def stage_for_implementation(implementation: str) -> WorkflowStage:
    """Return the principal public stage for an internal command."""
    return next(stage for stage in WORKFLOW_STAGES if implementation in stage.implementations)
