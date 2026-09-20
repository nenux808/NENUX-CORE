import inspect
import unittest

import main


class TestRagRuntimePolicy(unittest.TestCase):
    def test_agent_blocks_implicit_indexing(self):
        source = inspect.getsource(main.run_agent)
        self.assertIn("document_indexing_requested(user_input)", source)
        self.assertIn("Use search_documents directly", source)

    def test_process_request_skips_semantic_memory_for_document_tools(self):
        source = inspect.getsource(main.process_user_request)
        self.assertIn('"search_documents"', source)
        self.assertIn("non_memory_tools_used", source)
        self.assertIn("not non_memory_tools_used", source)


if __name__ == "__main__":
    unittest.main()
