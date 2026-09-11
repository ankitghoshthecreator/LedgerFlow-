"""
Abstract EventBus interface.

Both the in-process and Kafka implementations satisfy this contract.
Business logic only ever references this base — never the concrete class.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.domain.events import DomainEvent

T = TypeVar("T", bound=DomainEvent)
Handler = Callable[[DomainEvent], Awaitable[None]]


class EventBus(ABC):
    """Abstract event bus — publish/subscribe over domain events."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all registered subscribers."""

    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: Handler) -> None:
        """Register an async handler for a specific event type."""

    @abstractmethod
    async def start(self) -> None:
        """Start the bus (open connections, start consumers, etc.)."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the bus."""
