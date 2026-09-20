import unittest

from core.media_resolver import (
    _collapse_spelled_tokens,
    select_best_youtube_result,
)


class TestMediaResolver(unittest.TestCase):
    def test_collapses_spelled_artist_name(self):
        self.assertEqual(
            _collapse_spelled_tokens("S-H-A-N-P-U-T-H-A"),
            "SHANPUTHA",
        )

    def test_prefers_artist_and_title_match_over_first_result(self):
        search_result = {
            "results": [
                {
                    "title": "Trillium - YouTube",
                    "url": "https://www.youtube.com/watch?v=rzqkTRkddzo",
                    "snippet": "Trillium by S3RL",
                },
                {
                    "title": "Shan Putha - The Thrillium (Official Music Video) | The Thrillium Album - YouTube",
                    "url": "https://www.youtube.com/watch?v=xelLMC-z_e8",
                    "snippet": "Shan Putha official music video",
                },
            ]
        }

        selected = select_best_youtube_result(
            "play Trillium by Sean Putta",
            search_result,
        )

        self.assertIsNotNone(selected)
        self.assertEqual(
            selected["url"],
            "https://www.youtube.com/watch?v=xelLMC-z_e8",
        )


if __name__ == "__main__":
    unittest.main()
