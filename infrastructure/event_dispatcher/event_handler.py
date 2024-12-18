import asyncio
import logging
from collections import defaultdict, deque
from functools import partial
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Type, Union

from core.commands._base import Command, Status
from core.events._base import Event
from core.queries._base import Query
from core.result import Result
from core.tasks._base import Task

HandlerType = Union[partial, Callable[..., Any]]


logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, timeout: int = 15):
        self._event_handlers: Dict[Type[Event], List[HandlerType]] = defaultdict(list)
        self._dlq: Deque[Tuple[Event, Exception]] = deque(maxlen=100)
        self.timeout = timeout

    @property
    def dlq(self):
        return self._dlq

    def register(
        self,
        event_class: Type[Event],
        handler: HandlerType,
        filter_func: Optional[Callable[[Event], bool]] = None,
    ) -> None:
        self._event_handlers[event_class].append((handler, filter_func))

    def unregister(self, event_class: Type[Event], handler: HandlerType) -> None:
        self._event_handlers[event_class] = [
            (h, filter_fn)
            for h, filter_fn in self._event_handlers.get(event_class, [])
            if h != handler
        ]

    async def handle_event(self, event: Event, *args, **kwargs) -> None:
        handlers = self._event_handlers.get(type(event), [])

        for handler, filter_fn in handlers:
            if not filter_fn or filter_fn(event):
                await self._call_handler(handler, event, *args, **kwargs)

    async def _call_handler(
        self, handler: HandlerType, event: Event, *args, **kwargs
    ) -> None:
        try:
            if isinstance(event, Task):
                response = asyncio.create_task(
                    self._execute_handler(handler, event, *args, **kwargs)
                )
            else:
                response = await asyncio.wait_for(
                    self._execute_handler(handler, event, *args, **kwargs),
                    timeout=self.timeout,
                )

            self._handle_event_response(event, response)
        except Exception as e:
            self._handle_event_error(handler, event, e)

    async def _execute_handler(
        self, handler: HandlerType, event: Event, *args, **kwargs
    ) -> None:
        if asyncio.iscoroutinefunction(handler):
            return await handler(event, *args, **kwargs)
        return await asyncio.to_thread(handler, event, *args, **kwargs)

    def _handle_event_response(self, event: Event, response: Any) -> None:
        if isinstance(event, Query):
            event.set_response(Result.Ok(response))
        elif isinstance(event, Command):
            event.executed(Result.Ok(Status.SUCCESS))
        elif isinstance(event, Task):
            event.set_task(response)

    def _handle_event_error(
        self, handler: HandlerType, event: Event, error: Exception
    ) -> None:
        if isinstance(event, Query):
            event.set_response(Result.Err(error))
        elif isinstance(event, Command):
            event.executed(Result(Status.FAIL, error))
        elif isinstance(event, Task):
            event.set_task(asyncio.create_task(asyncio.sleep(0.00001)))

        self._dlq.append((event, error))

        logger.error(
            f"Exception encountered in event {event}:{handler} {error}. Event added to dead letter queue."
        )
