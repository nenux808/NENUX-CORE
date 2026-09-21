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

    @patch("core.planner.chat")
    def test_default_profile_change_skips_model_planner(self, mock_chat):
        steps = create_plan("set first profile as default")

        self.assertEqual(
            steps,
            [
                "List available local Chrome profiles using list_chrome_profiles",
                "Set the selected Chrome profile as default using set_default_chrome_profile",
            ],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_pause_uses_media_control_plan(self, mock_chat):
        self.assertEqual(
            create_plan("pause it"),
            ["Pause or resume current media using media_control"],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_close_tab_uses_chrome_tab_control_plan(self, mock_chat):
        self.assertEqual(
            create_plan("close this tab"),
            ["Close the current Chrome tab using chrome_tab_control"],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_open_gmail_is_deterministic(self, mock_chat):
        self.assertEqual(
            create_plan("open Gmail"),
            ["Open Gmail in Chrome using open_gmail"],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_open_vscode_is_deterministic(self, mock_chat):
        self.assertEqual(
            create_plan("open VS Code"),
            ["Open Visual Studio Code using open_vscode"],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_open_chrome_is_deterministic(self, mock_chat):
        self.assertEqual(
            create_plan("open Chrome"),
            ["Open Google Chrome using open_chrome"],
        )
        mock_chat.assert_not_called()

    @patch("core.planner.chat")
    def test_youtube_search_is_deterministic(self, mock_chat):
        steps = create_plan("search weekends playlist in youtube")

        self.assertEqual(
            steps,
            [
                'Open YouTube search results for "weekends playlist" in Chrome using open_youtube_search'
            ],
        )
        mock_chat.assert_not_called()


if __name__ == "__main__":
    unittest.main()
