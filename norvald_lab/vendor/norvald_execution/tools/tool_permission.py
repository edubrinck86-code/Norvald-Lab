"""Disponibilidade de uma ferramenta para quem executa.

Três níveis, e a diferença entre eles é de quem decide: desabilitada não
chega ao modelo; disponível chega e o modelo decide se usa; obrigatória
o fluxo exige. A LLM escolhe dentro do que foi disponibilizado, nunca
além.
"""

from dataclasses import dataclass

DISABLED = "disabled"
AVAILABLE = "available"
REQUIRED = "required"
AVAILABILITY_LEVELS = (DISABLED, AVAILABLE, REQUIRED)


@dataclass(frozen=True)
class ToolPermission:
    tool_name: str
    level: str = AVAILABLE

    def __post_init__(self) -> None:
        if self.level not in AVAILABILITY_LEVELS:
            raise ValueError(
                f"Nível de disponibilidade inválido: '{self.level}'. "
                f"Use um de: {', '.join(AVAILABILITY_LEVELS)}."
            )

    @property
    def enabled(self) -> bool:
        return self.level != DISABLED

