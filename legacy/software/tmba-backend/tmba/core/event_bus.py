from collections import defaultdict
from threading import Lock
from typing import Any, Callable


EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """Einfacher interner Ereignisverteiler für TMBA-OS."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        """Registriert eine Funktion für ein Ereignis."""

        normalized_event_name = self._normalize_event_name(event_name)

        with self._lock:
            if handler not in self._handlers[normalized_event_name]:
                self._handlers[normalized_event_name].append(handler)

    def unsubscribe(
        self,
        event_name: str,
        handler: EventHandler,
    ) -> None:
        """Entfernt eine registrierte Funktion."""

        normalized_event_name = self._normalize_event_name(event_name)

        with self._lock:
            handlers = self._handlers.get(normalized_event_name, [])

            if handler in handlers:
                handlers.remove(handler)

    def publish(
        self,
        event_name: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Veröffentlicht ein Ereignis an alle registrierten Empfänger."""

        normalized_event_name = self._normalize_event_name(event_name)
        event_data = data.copy() if data is not None else {}

        with self._lock:
            handlers = self._handlers.get(
                normalized_event_name,
                [],
            ).copy()

        for handler in handlers:
            handler(event_data)

    @staticmethod
    def _normalize_event_name(event_name: str) -> str:
        """Vereinheitlicht einen Ereignisnamen."""

        normalized_event_name = event_name.strip().lower()

        if not normalized_event_name:
            raise ValueError("Der Ereignisname darf nicht leer sein.")

        return normalized_event_name


event_bus = EventBus()