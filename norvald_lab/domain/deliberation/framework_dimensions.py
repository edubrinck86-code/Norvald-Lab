"""Dimensões do baseline do Framework — reexportação.

Movido para a Documental Engine (ADR-D-001): o vocabulário do Framework
é anterior e mais amplo que a deliberação, e o Builder precisa dele sem
poder importar o Studio.

Este módulo reexporta a cópia vendorizada para que os consumidores
internos não precisem mudar de import de uma vez. A fonte é
`backend/vendor/documental_engine/framework/`, e mudança de conteúdo
acontece no repositório de origem, nunca aqui.
"""

from norvald_lab.vendor.documental_engine.framework.framework_dimensions import *  # noqa: F401,F403
from norvald_lab.vendor.documental_engine.framework.framework_dimensions import (  # noqa: F401
    BASELINE_DIMENSIONS,
    build_baseline_registry,
    dimension_id_of,
    _ALL_SEGMENT_SUBDIMENSIONS,
)

