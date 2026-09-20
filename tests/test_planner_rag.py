import unittest
from unittest.mock import patch

from core.planner import create_plan


class TestLocalDocumentPlanning(unittest.TestCase):
    @patch("core.planner.chat")
    def test_local_document_question_skips_model_planner(self, mock_chat):
        steps = create_plan(
            "what does my document say the codename for the retrieval system is?"
        )

        self.assertEqual(
            steps,
            [
                "Search the indexed workspace documents using search_documents and answer from the retrieved evidence"
            ],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_workspace_index_goal_skips_model_planner(self, mock_chat):
        steps = create_plan("index my workspace documents")

        self.assertEqual(
            steps,
            [
                "Index all supported workspace documents using index_workspace_documents"
            ],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_media_playback_skips_model_planner(self, mock_chat):
        steps = create_plan("play Ocean Eyes by Billie Eilish")

        self.assertEqual(
            steps,
            [
                "Search the web for the most relevant official YouTube video for the requested media",
                "Open the verified YouTube video in Chrome using open_chrome_url",
            ],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_chrome_profile_listing_skips_model_planner(self, mock_chat):
        steps = create_plan("list my Chrome profiles")

        self.assertEqual(
            steps,
            ["List available local Chrome profiles using list_chrome_profiles"],
        )
        mock_chat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
