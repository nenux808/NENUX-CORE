import unittest

from core.router import route_request


class TestRequestRouter(unittest.TestCase):
    def test_identity_question_is_conversation(self):
        self.assertEqual(route_request("what is your name?"), "conversation")

    def test_memory_question_routes_to_memory(self):
        self.assertEqual(route_request("what did we do previously?"), "memory")

    def test_execution_request_routes_to_agent(self):
        self.assertEqual(route_request("run the Python script"), "agent_task")


if __name__ == "__main__":
    unittest.main()
