"""E-00 non-destructive pinned converter smoke fixture.

Run from repository root with `python -m unittest discover -s tests -p 'test_e00_*.py'`.
This tests existing output shape; it does NOT assert full FHIR conformance or PIQI fidelity.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.fhir_convert_backend import convert_message_to_bundle, split_messages

ROOT = Path(__file__).resolve().parents[1]


class E00OriginalConverterBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (ROOT / 'tests' / 'fixtures' / 'e00' / 'hl7_smoke_messages.hl7').read_text(encoding='utf-8')
        cls.messages = split_messages(raw)
        cls.baseline = json.loads((ROOT / 'docs' / 'baselines' / 'e00_converter_smoke_summary.json').read_text(encoding='utf-8'))

    def test_four_messages_are_split(self):
        self.assertEqual(len(self.messages), 4)

    def test_original_converter_summary_matches_frozen_control(self):
        from collections import Counter
        actual = []
        for i, message in enumerate(self.messages, start=1):
            bundle, typ = convert_message_to_bundle(message)
            resources = [e['resource'] for e in bundle['entry']]
            observations = [r for r in resources if r['resourceType'] == 'Observation']
            actual.append({
                'message_index': i,
                'message_type': typ,
                'resource_types': dict(sorted(Counter(r['resourceType'] for r in resources).items())),
                'observation_value_kinds': [next((k for k in (
                    'valueString', 'valueQuantity', 'valueCodeableConcept', 'valueDateTime'
                ) if k in obs), 'NO_VALUE') for obs in observations],
                'fhir_bundle_type': bundle['type'],
            })
        self.assertEqual(actual, self.baseline['results'])

    def test_historical_adt_cwe_falls_back_to_string(self):
        bundle, typ = convert_message_to_bundle(self.messages[0])
        obs = next(e['resource'] for e in bundle['entry'] if e['resource']['resourceType'] == 'Observation')
        self.assertIn('valueString', obs)
        self.assertNotIn('valueCodeableConcept', obs)

    def test_historical_orm_has_no_order_resource(self):
        bundle, typ = convert_message_to_bundle(self.messages[3])
        self.assertEqual(typ, 'ORM^O01')
        self.assertEqual({e['resource']['resourceType'] for e in bundle['entry']}, {'Patient', 'MessageHeader'})

    def test_repeatable_summary_ignores_generated_resource_ids(self):
        # Result identities use random UUIDs; this contract intentionally freezes
        # only deterministic legacy shape and value-type information.
        self.test_original_converter_summary_matches_frozen_control()


if __name__ == '__main__':
    unittest.main()
