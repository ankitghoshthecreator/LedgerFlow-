"""
In-process async event bus — Phase 1 implementation.

Uses asyncio queues for reliable in-order delivery.
Supports multiple handlers per event type.
Drop-in replacement for Kafka: changing EVENT_BUS_BACKEND env var
switches to the Kafka implementation without touching business code.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from app.domain.events import DomainEvent
from app.event_bus.base import EventBus, Handler

logger = logging.getLogger(__name__)


class InProcessEventBus(EventBus):
    """
    Thread-safe in-process event bus backed by asyncio.Queue.
    Suitable for local dev and single-process deployments.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._running = False
        self._worker_task: asyncio.Task | None = None

    def subscribe(self, event_type: type[DomainEvent], handler: Handler) -> None:
        key = event_type.__name__
        self._handlers[key].append(handler)
        logger.debug("Subscribed %s to %s", handler.__qualname__, key)

    async def publish(self, event: DomainEvent) -> None:
        logger.info("Publishing event: %s [app=%s]",
                    type(event).__name__,
                    getattr(event, "application_id", "—"))
        await self._queue.put(event)

    async def start(self) -> None:
        self._running = True
        self._worker_task = asyncio.create_task(self._dispatch_loop(), name="event-bus-worker")
        logger.info("InProcessEventBus started")

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("InProcessEventBus stopped")

    async def _dispatch_loop(self) -> None:
        """Continuously drain the queue and dispatch to handlers."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Unhandled error in event dispatch loop: %s", exc)

    async def _dispatch(self, event: DomainEvent) -> None:
        key = type(event).__name__
        handlers = self._handlers.get(key, [])
        if not handlers:
            logger.warning("No handlers for event type: %s", key)
            return
        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                logger.exception(
                    "Handler %s failed for event %s: %s",
                    handler.__qualname__, key, exc
                )
