import unittest

from core.evaluator import _enforce_tool_action_matching


class TestEvaluatorRagToolMatching(unittest.TestCase):
    def test_search_documents_completes_local_rag_step(self):
        planned = [
            {
                "step_id": 1,
                "description": (
                    "Search the indexed workspace documents using search_documents "
                    "and answer from the retrieved evidence"
                ),
            }
        ]
        trace = [
            {
                "tool": "search_documents",
                "result": {
                    "success": True,
                    "results": [
                        {
                            "source_path": "nenux_test.txt",
                            "content": "The codename is Atlas.",
                        }
                    ],
                },
            }
        ]
        evaluation = [
            {
                "step_id": 1,
                "status": "completed",
                "reason": "Relevant document evidence was retrieved.",
            }
        ]

        result = _enforce_tool_action_matching(planned, trace, evaluation)
        self.assertEqual(result[0]["status"], "completed")

    def test_missing_search_documents_keeps_rag_step_pending(self):
        planned = [
            {
                "step_id": 1,
                "description": (
                    "Search the indexed workspace documents using search_documents "
                    "and answer from the retrieved evidence"
                ),
            }
        ]

        result = _enforce_tool_action_matching(
            planned,
            [],
            [{"step_id": 1, "status": "completed", "reason": "claimed"}],
        )

        self.assertEqual(result[0]["status"], "pending")
        self.assertIn("search_documents", result[0]["reason"])


if __name__ == "__main__":
    unittest.main()
