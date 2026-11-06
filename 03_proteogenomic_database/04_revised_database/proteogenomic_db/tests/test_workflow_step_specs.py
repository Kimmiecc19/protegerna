"""The per-step specification must stay in sync with each step's real CLI parser."""
import unittest

import proteogenomic_workflow as workflow


class StepSpecConsistencyTests(unittest.TestCase):
    def test_every_spec_option_is_a_real_parser_option(self):
        for step, spec in workflow.STEPS.items():
            options = workflow._parser_keys(step)
            for kind, keys in (("common", spec.common), ("inputs", spec.inputs), ("outputs", spec.outputs)):
                missing = sorted(set(keys) - options)
                self.assertEqual(missing, [], f"[{step}] {kind} options not accepted by its parser: {missing}")

    def test_common_options_are_declared_common_keys(self):
        for step, spec in workflow.STEPS.items():
            self.assertLessEqual(set(spec.common), set(workflow.COMMON_KEYS), step)

    def test_directory_outputs_are_outputs(self):
        for step, spec in workflow.STEPS.items():
            self.assertLessEqual(set(spec.directory_outputs), set(spec.outputs), step)

    def test_legacy_views_match_the_spec(self):
        self.assertEqual(list(workflow.STEP_MODULES), list(workflow.STEPS))
        for step, spec in workflow.STEPS.items():
            self.assertEqual(workflow.STEP_MODULES[step], spec.module)
            self.assertEqual(workflow.OUTPUT_KEYS[step], set(spec.outputs))

    def test_parsers_are_built_once(self):
        self.assertIs(workflow._parser("merge"), workflow._parser("merge"))


if __name__ == "__main__":
    unittest.main()
