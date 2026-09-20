import unittest

from main import _tool_result_for_context
from config import TOOL_RESULT_CONTEXT_CHARS


class TestContextBudget(unittest.TestCase):
    def test_large_tool_result_is_truncated_for_model_context(self):
        result = {
            "success": True,
            "text": "x" * (TOOL_RESULT_CONTEXT_CHARS * 2),
        }

        compact = _tool_result_for_context(result)

        self.assertIn("truncated", compact)
        self.assertLess(
            len(compact),
            TOOL_RESULT_CONTEXT_CHARS + 100,
        )

    def test_small_tool_result_is_preserved(self):
        result = {"success": True, "value": 42}

        compact = _tool_result_for_context(result)

        self.assertIn('"value": 42', compact)
        self.assertNotIn("truncated", compact)


if __name__ == "__main__":
    unittest.main()
