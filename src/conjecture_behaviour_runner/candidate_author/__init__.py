"""Portable candidate soak-path author (Scenario precursor to Script).

Host supplies vocabulary (kinds, competing leaves, incidents, matrix cells).
This package does **not** import product agents.

::

    from conjecture_behaviour_runner.candidate_author import (
        HostVocabulary,
        author_candidates,
        write_candidate_scenarios,
    )

    vocab = HostVocabulary(
        sole_continue_kinds=frozenset({\"invoice_intake\"}),
        kinds_suppress_surface=frozenset({\"invoice_intake\"}),
        foreign_capability_leaves=frozenset({\"cyber_assessment\"}),
        foreign_library_leaves=frozenset({\"list_records\"}),
        kind_to_owner={\"invoice_intake\": \"invoice_intake\"},
    )
    paths = author_candidates(vocabulary=vocab)
    write_candidate_scenarios(paths, \"out/scenarios\")
"""
from __future__ import annotations

from conjecture_behaviour_runner.candidate_author.engine import (
    author_candidates,
    format_candidates_markdown,
    paths_from_incidents,
    paths_from_matrix_cells,
    paths_from_residuals,
    paths_from_sole_continue_x_foreign,
)
from conjecture_behaviour_runner.candidate_author.invent import (
    invent_all,
    invent_exclusive_owner_conflicts,
    invent_polarity_flips_from_seals,
)
from conjecture_behaviour_runner.candidate_author.invent_config import (
    InventConfig,
    load_geometry_propose_prompt,
    load_invent_config,
    make_env_llm_complete,
)
from conjecture_behaviour_runner.candidate_author.invent_propose import (
    GeometryProposal,
    ProposeResult,
    backcheck_proposal,
    build_propose_user_prompt,
    check_laws,
    check_physics,
    merge_proposals_into_vocab,
    parse_proposals,
    propose_geometry,
)
from conjecture_behaviour_runner.candidate_author.models import (
    CandidatePath,
    HostIncident,
    HostVocabulary,
    MatrixCell,
    ResidualProbe,
    blocks_foreign_leaf,
)
from conjecture_behaviour_runner.candidate_author.scenario_emit import (
    candidate_to_scenario_dict,
    scenario_id_for,
    scenario_to_yaml,
    write_candidate_scenarios,
)
from conjecture_behaviour_runner.candidate_author.template_load import (
    load_example_template_bundle,
    load_incidents_yaml,
    load_matrix_yaml,
    load_residuals_yaml,
    load_vocabulary_yaml,
)

__all__ = [
    "CandidatePath",
    "HostIncident",
    "HostVocabulary",
    "MatrixCell",
    "ResidualProbe",
    "author_candidates",
    "blocks_foreign_leaf",
    "candidate_to_scenario_dict",
    "format_candidates_markdown",
    "GeometryProposal",
    "InventConfig",
    "ProposeResult",
    "backcheck_proposal",
    "build_propose_user_prompt",
    "check_laws",
    "check_physics",
    "invent_all",
    "invent_exclusive_owner_conflicts",
    "invent_polarity_flips_from_seals",
    "load_geometry_propose_prompt",
    "load_invent_config",
    "make_env_llm_complete",
    "merge_proposals_into_vocab",
    "parse_proposals",
    "propose_geometry",
    "load_example_template_bundle",
    "load_incidents_yaml",
    "load_matrix_yaml",
    "load_residuals_yaml",
    "load_vocabulary_yaml",
    "paths_from_incidents",
    "paths_from_matrix_cells",
    "paths_from_residuals",
    "paths_from_sole_continue_x_foreign",
    "scenario_id_for",
    "scenario_to_yaml",
    "write_candidate_scenarios",
]
