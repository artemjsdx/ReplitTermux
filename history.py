"""
history.py — Command history store.
S: One responsibility — store and retrieve command records.
O: MaxHistory limit configurable at construction time.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List


@dataclass
class CommandRecord:
    cmd:     str
    out:     str
    code:    int
    elapsed: float
    ts:      str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    def to_dict(self) -> dict:
        return asdict(self)


class CommandHistory:
    def __init__(self, max_size: int = 200) -> None:
        self._max  = max_size
        self._log: List[CommandRecord] = []

    def append(self, record: CommandRecord) -> None:
        self._log.append(record)
        if len(self._log) > self._max:
            self._log.pop(0)

    def tail(self, n: int = 50) -> List[CommandRecord]:
        return self._log[-n:]

    def last(self) -> CommandRecord | None:
        return self._log[-1] if self._log else None

    def __len__(self) -> int:
        return len(self._log)
