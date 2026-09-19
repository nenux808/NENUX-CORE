import unittest

from core.evaluator import _enforce_tool_action_matching


class TestEvaluatorToolMatching(unittest.TestCase):
    def test_web_search_does_not_complete_fetch_step(self):
        planned = [
            {"step_id": 1, "description": "Search the web for the song"},
            {"step_id": 2, "description": "Fetch the actual source page"},
        ]
        trace = [
            {"tool": "web_search", "result": {"success": True}},
        ]
        model_evaluation = [
            {"step_id": 1, "status": "completed", "reason": "searched"},
            {"step_id": 2, "status": "completed", "reason": "claimed fetched"},
        ]

        result = _enforce_tool_action_matching(
            planned,
            trace,
            model_evaluation,
        )

        self.assertEqual(result[0]["status"], "completed")
        self.assertEqual(result[1]["status"], "pending")
        self.assertIn("web_fetch", result[1]["reason"])


if __name__ == "__main__":
    unittest.main()
