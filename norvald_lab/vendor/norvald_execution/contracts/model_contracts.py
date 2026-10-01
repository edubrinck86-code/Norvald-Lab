from dataclasses import dataclass, field


REASONING_EFFORT_LEVELS = ("off", "low", "medium", "high")


@dataclass
class ModelInfo:
    id: str
    display_name: str
    vendor: str = ""
    raw_metadata: dict = field(default_factory=dict)

