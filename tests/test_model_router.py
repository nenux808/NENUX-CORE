import unittest

import config
from core.model_router import select_model


class TestModelRouter(unittest.TestCase):
    def test_desktop_intent_uses_fast_tier(self):
        decision = select_model(
            "close all tabs",
            route="agent_task",
            desktop_intent="close_all_tabs",
        )

        self.assertEqual(decision.tier, "FAST")
        self.assertEqual(decision.model, config.FAST_MODEL)

    def test_short_conversation_uses_fast_tier(self):
        decision = select_model(
            "hello clara",
            route="conversation",
        )

        self.assertEqual(decision.tier, "FAST")

    def test_general_agent_task_uses_main_tier(self):
        decision = select_model(
            "Search the web for the latest Python release.",
            route="retrieval",
        )

        self.assertEqual(decision.tier, "MAIN")
        self.assertEqual(decision.model, config.CHAT_MODEL)

    def test_debugging_request_uses_heavy_tier(self):
        decision = select_model(
            "Debug this code and investigate the root cause of the failure.",
            route="agent_task",
        )

        self.assertEqual(decision.tier, "HEAVY")
        self.assertEqual(decision.model, config.HEAVY_MODEL)

    def test_architecture_request_uses_heavy_tier(self):
        decision = select_model(
            "Design the architecture for a complex multi-step agent system.",
            route="agent_task",
        )

        self.assertEqual(decision.tier, "HEAVY")

    def test_tiers_default_without_extra_model_downloads(self):
        self.assertTrue(config.FAST_MODEL)
        self.assertTrue(config.CHAT_MODEL)
        self.assertTrue(config.HEAVY_MODEL)


if __name__ == "__main__":
    unittest.main()
