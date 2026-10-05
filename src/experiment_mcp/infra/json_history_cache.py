"""JSON file cache adapter for price histories."""

import json
import os
import tempfile
import time
from pathlib import Path

from experiment_mcp.core.models import PriceBar, PriceHistory


class JsonFileHistoryCache:
    def __init__(self, cache_dir: Path, ttl_seconds: int = 900) -> None:
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> PriceHistory | None:
        path = self.cache_dir / f"{key}.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - payload["fetched_at"] > self.ttl_seconds:
                return None
            bars = tuple(
                PriceBar(timestamp=item["timestamp"], values=item["values"])
                for item in payload["bars"]
            )
            return PriceHistory(ticker=payload["ticker"], bars=bars)
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def set(self, key: str, history: PriceHistory) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at": time.time(),
            "ticker": history.ticker,
            "bars": [{"timestamp": bar.timestamp, "values": bar.values} for bar in history.bars],
        }
        descriptor, temporary_path = tempfile.mkstemp(dir=self.cache_dir, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as cache_file:
                json.dump(payload, cache_file, allow_nan=False)
            os.replace(temporary_path, self.cache_dir / f"{key}.json")
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)
