import unittest

from core.evaluator import _enforce_tool_action_matching


class TestPcPlaybackEvaluation(unittest.TestCase):
    def test_profile_selection_is_not_treated_as_opened(self):
        planned = [
            {
                "step_id": 1,
                "description": "Open the verified YouTube video in Chrome using open_chrome_url",
            }
        ]
        trace = [
            {
                "tool": "open_chrome_url",
                "result": {
                    "success": True,
                    "opened": False,
                    "needs_profile_selection": True,
                },
            }
        ]
        model_eval = [
            {"step_id": 1, "status": "completed", "reason": "tool was called"}
        ]

        result = _enforce_tool_action_matching(planned, trace, model_eval)

        self.assertEqual(result[0]["status"], "pending")

    def test_confirmed_chrome_launch_can_complete(self):
        planned = [
            {
                "step_id": 1,
                "description": "Open the verified YouTube video in Chrome using open_chrome_url",
            }
        ]
        trace = [
            {
                "tool": "open_chrome_url",
                "result": {
                    "success": True,
                    "opened": True,
                    "profile_directory": "Default",
                },
            }
        ]
        model_eval = [
            {"step_id": 1, "status": "completed", "reason": "Chrome opened"}
        ]

        result = _enforce_tool_action_matching(planned, trace, model_eval)

        self.assertEqual(result[0]["status"], "completed")


if __name__ == "__main__":
    unittest.main()
