import unittest
from unittest.mock import patch

from core.router import route_request


class TestRequestRouter(unittest.TestCase):
    def test_identity_question_is_conversation(self):
        self.assertEqual(route_request("what is your name?"), "conversation")

    def test_memory_question_routes_to_memory(self):
        self.assertEqual(route_request("what did we do previously?"), "memory")

    def test_execution_request_routes_to_agent(self):
        self.assertEqual(route_request("run the Python script"), "agent_task")

    def test_current_information_routes_to_agent(self):
        self.assertEqual(
            route_request("what is the weather in Melbourne right now?"),
            "agent_task",
        )

    def test_explicit_web_search_routes_to_agent(self):
        self.assertEqual(
            route_request("search the web for NENUX Core"),
            "agent_task",
        )

    def test_lyrics_request_routes_to_retrieval(self):
        self.assertEqual(
            route_request("do you remember any lyric from Ocean Eyes?"),
            "retrieval",
        )

    @patch("core.router._model_route", return_value="retrieval")
    def test_obscure_youtube_channel_can_route_to_retrieval(self, mock_route):
        self.assertEqual(
            route_request("what do you know about SL vlog, YouTube channel?"),
            "retrieval",
        )
        mock_route.assert_called_once()

    @patch("core.router._model_route", return_value="conversation")
    def test_common_entity_question_can_remain_conversation(self, mock_route):
        self.assertEqual(
            route_request("what is Python?"),
            "conversation",
        )
        mock_route.assert_called_once()


if __name__ == "__main__":
    unittest.main()
