"""
Kafka event bus stub — Phase 2+ implementation.

Satisfies the same EventBus interface. Swap in by setting:
    EVENT_BUS_BACKEND=kafka
in your .env file.

Requires: aiokafka>=0.10.0 (add to requirements.txt when enabling)
"""
from __future__ import annotations

import json
import logging

from app.domain.events import DomainEvent
from app.event_bus.base import EventBus, Handler

logger = logging.getLogger(__name__)


class KafkaEventBus(EventBus):
    """
    Kafka-backed event bus.
    Phase 1: stub that raises NotImplementedError.
    Phase 2+: replace body with aiokafka producer/consumer.
    """

    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: Handler) -> None:
        key = event_type.__name__
        self._handlers.setdefault(key, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        # TODO Phase 2: produce to Kafka topic = event.event_type
        # topic = event.event_type.value.replace(".", "-")
        # await self._producer.send_and_wait(topic, json.dumps(event.to_dict()).encode())
        raise NotImplementedError(
            "Kafka bus not yet wired. Set EVENT_BUS_BACKEND=in_process for Phase 1."
        )

    async def start(self) -> None:
        logger.info("KafkaEventBus.start() — stub, not yet implemented")

    async def stop(self) -> None:
        logger.info("KafkaEventBus.stop() — stub, not yet implemented")
