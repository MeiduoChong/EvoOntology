"""Read-only visualization of an EvoOntology ontology version.

Public entry point: :func:`visualize`. Claude Code (``/evo-visualize``) and
Codex (``$evo-visualize``) both call this same API.
"""

from .renderer import (
    ACTIVE,
    CYTOSCAPE_VERSION,
    RELATION_TYPES,
    VISUALIZATION_FILENAME,
    VISUALIZATIONS_DIRNAME,
    build_content_elements,
    build_schema_view,
    build_tool_view,
    load_ontology,
    render_html,
    resolve_version,
    visualize,
)

__all__ = [
    "ACTIVE",
    "CYTOSCAPE_VERSION",
    "RELATION_TYPES",
    "VISUALIZATION_FILENAME",
    "VISUALIZATIONS_DIRNAME",
    "visualize",
    "resolve_version",
    "load_ontology",
    "build_content_elements",
    "build_schema_view",
    "build_tool_view",
    "render_html",
]
