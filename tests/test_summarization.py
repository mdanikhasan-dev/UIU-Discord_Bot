import asyncio
import unittest

from services.summarization import (
    MAX_INPUT_CHARACTERS,
    SummarizationError,
    summarize,
    summarize_locally,
)


LONG_TEXT = (
    "The engineering team reviewed the service after three connection failures. "
    "They found that every request created a new database connection. "
    "The team introduced connection pooling and a bounded retry policy. "
    "Load testing then reduced median latency from 420 milliseconds to 130 milliseconds. "
    "The release remains behind a feature flag until the error rate stays below one percent. "
    "The next review is scheduled for Monday with operations and support."
)


class LocalSummarizerTests(unittest.TestCase):
    def test_concise_summary_is_shorter_than_input(self) -> None:
        result = summarize_locally(LONG_TEXT, "concise")
        self.assertEqual(result.engine, "private local")
        self.assertLess(len(result.text), len(LONG_TEXT))
        self.assertFalse(result.input_truncated)

    def test_bullet_style_uses_bullets(self) -> None:
        result = summarize_locally(LONG_TEXT, "bullets")
        self.assertTrue(result.text.startswith("• "))
        self.assertLessEqual(result.text.count("• "), 5)

    def test_large_input_is_bounded(self) -> None:
        result = summarize_locally((LONG_TEXT + " ") * 1000, "concise")
        self.assertTrue(result.input_truncated)
        self.assertLessEqual(len(result.text), 1800)

    def test_empty_input_rejected(self) -> None:
        with self.assertRaises(SummarizationError):
            summarize_locally("   \n ", "concise")

    def test_input_limit_is_not_zero(self) -> None:
        self.assertGreaterEqual(MAX_INPUT_CHARACTERS, 10_000)

    def test_short_run_on_text_is_cleaned_instead_of_echoed(self) -> None:
        source = (
            "i have no life i dreamed of having free time and i want to be the best "
            "of my version but i cant"
        )
        result = summarize_locally(source, "concise")
        self.assertEqual(result.label, "Cleaned brief")
        self.assertNotEqual(result.text, source)
        self.assertIn("I can't", result.text)
        self.assertIn("best version of myself", result.text)
        self.assertNotIn("and.", result.text)
        self.assertNotIn("but.", result.text)
        self.assertNotIn(",,", result.text)
        self.assertTrue(result.text.endswith("."))

    def test_ai_engine_requires_owner_configuration(self) -> None:
        with self.assertRaisesRegex(SummarizationError, "GROQ_API_KEY"):
            asyncio.run(
                summarize(
                    LONG_TEXT,
                    "concise",
                    "ai",
                    groq_api_key="",
                    groq_model="llama-3.1-8b-instant",
                )
            )


if __name__ == "__main__":
    unittest.main()
