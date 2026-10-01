from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any, AsyncIterator


class ArofExperimentEventHub:
    """Telemetria efêmera para a UI do Runner.

    Não é dataset e não participa de nenhuma métrica. Um histórico curto em
    memória evita perder os primeiros eventos quando o POST começa antes de
    o EventSource terminar o handshake.
    """

    def __init__(self, history_limit: int = 200) -> None:
        self._subscribers: dict[
            str, set[asyncio.Queue[dict[str, Any]]]
        ] = defaultdict(set)
        self._history: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._sequence: dict[str, int] = defaultdict(int)
        self._history_limit = max(20, history_limit)

    def publish(
        self, experiment_id: str, event: str, data: dict[str, Any]
    ) -> None:
        self._sequence[experiment_id] += 1
        payload = {
            "id": self._sequence[experiment_id],
            "event": event,
            "data": dict(data),
        }
        history = self._history[experiment_id]
        history.append(payload)
        if len(history) > self._history_limit:
            del history[:-self._history_limit]
        for queue in tuple(self._subscribers.get(experiment_id, ())):
            queue.put_nowait(payload)

    @staticmethod
    def _frame(payload: dict[str, Any]) -> str:
        body = json.dumps(payload, ensure_ascii=False, default=str)
        return (
            f"id: {payload['id']}\n"
            f"event: {payload['event']}\n"
            f"data: {body}\n\n"
        )

    async def stream(
        self, experiment_id: str, last_event_id: int = 0
    ) -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers[experiment_id].add(queue)
        try:
            for payload in self._history.get(experiment_id, ()):
                if int(payload.get("id") or 0) > last_event_id:
                    yield self._frame(payload)
            while True:
                try:
                    payload = await asyncio.wait_for(
                        queue.get(), timeout=15
                    )
                    yield self._frame(payload)
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            self._subscribers[experiment_id].discard(queue)
            if not self._subscribers[experiment_id]:
                self._subscribers.pop(experiment_id, None)


_hub = ArofExperimentEventHub()


def get_arof_experiment_event_hub() -> ArofExperimentEventHub:
    return _hub

