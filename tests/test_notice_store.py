import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from services.notice_store import NoticeStore, NoticeStoreError


class NoticeStoreTests(unittest.TestCase):
    def test_configure_disable_and_mark_seen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = NoticeStore(Path(directory) / "notices.json")

            async def scenario() -> None:
                await store.configure(1001, 2001)
                state = await store.snapshot()
                self.assertEqual(state["1001"]["notice_channel_id"], 2001)
                await store.mark_seen(1001, ["https://www.uiu.ac.bd/notice/example/"])
                state = await store.snapshot()
                self.assertEqual(len(state["1001"]["seen_notices"]), 1)
                self.assertTrue(await store.disable(1001))
                self.assertFalse(await store.disable(1001))

            asyncio.run(scenario())

    def test_corrupt_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notices.json"
            path.write_text("not json", encoding="utf-8")
            store = NoticeStore(path)
            with self.assertRaises(NoticeStoreError):
                asyncio.run(store.configure(1001, 2001))
            self.assertEqual(path.read_text(encoding="utf-8"), "not json")

    def test_written_document_has_schema_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notices.json"
            store = NoticeStore(path)
            asyncio.run(store.configure(1001, 2001))
            state = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(state["version"], 1)


if __name__ == "__main__":
    unittest.main()
