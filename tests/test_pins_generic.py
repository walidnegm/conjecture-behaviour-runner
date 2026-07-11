"""Fix #4: CognitionPin is portable — product flags live in extras."""
from __future__ import annotations

import unittest

from conjecture_behaviour_runner import CognitionPin


class GenericPinTests(unittest.TestCase):
    def test_core_fields_only_on_dataclass(self) -> None:
        from dataclasses import fields

        names = {f.name for f in fields(CognitionPin)}
        # Must not bake product router flags into the public type.
        for banned in (
            "cost_estimate_request",
            "workflow_draft_request",
            "catalog_role_request",
            "product_concept_kind",
            "attachment_capability_request",
            "reset_request",
            "workflow_id",  # entity identity is observation.pins, not cognition
        ):
            self.assertNotIn(banned, names)

    def test_legacy_product_fields_fold_into_extras(self) -> None:
        pin = CognitionPin.from_dict(
            {
                "task_intent": "continue",
                "cost_estimate_request": True,
                "workflow_draft_request": False,
                "product_concept_kind": "scorecard",
            }
        )
        self.assertEqual(pin.task_intent, "continue")
        self.assertTrue(pin.extra("cost_estimate_request"))
        self.assertFalse(pin.extra("workflow_draft_request"))
        self.assertEqual(pin.extra("product_concept_kind"), "scorecard")
        # Not first-class attributes
        self.assertFalse(hasattr(pin, "cost_estimate_request"))

    def test_roundtrip_preserves_extras(self) -> None:
        pin = CognitionPin(
            task_intent="detour",
            discovery_kind="glossary",
            extras={"cost_estimate_request": True},
        )
        pin2 = CognitionPin.from_dict(pin.to_dict())
        self.assertEqual(pin2.task_intent, "detour")
        self.assertEqual(pin2.discovery_kind, "glossary")
        self.assertTrue(pin2.extra("cost_estimate_request"))


if __name__ == "__main__":
    unittest.main()
