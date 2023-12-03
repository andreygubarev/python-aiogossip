import asyncio
import collections
import fnmatch
import itertools

from .channel import Channel
from .errors import print_exception
from .gossip import Gossip

# from .message_pb2 import Message


class Handler:
    def __init__(self, topic, func, loop: asyncio.AbstractEventLoop):
        self._loop = loop

        self.topic = topic
        self.func = func
        self.chan = Channel(loop=self._loop)

        self.task = self._loop.create_task(self())
        self.task.add_done_callback(print_exception)
        self._hooks = []

    async def __call__(self):
        while True:
            message = await self.chan.recv()
            result = await self.func(message)

            if result is None:
                continue

            for hook in self._hooks:
                await hook(message, result)

    def hook(self, func):
        self._hooks.append(func)

    async def cancel(self):
        for hook in self._hooks:
            hook.cancel()
        await asyncio.gather(*self._hooks, return_exceptions=True)
        await self.chan.close()
        self.task.cancel()


class Broker:
    TIMEOUT = 10

    def __init__(self, gossip: Gossip, loop: asyncio.AbstractEventLoop = None):
        self._loop = loop or gossip.transport._loop

        self.gossip = gossip
        self._handlers = collections.defaultdict(list)

    async def listen(self):
        """Connect to the gossip network and start receiving messages."""
        async for message in self.gossip.recv():
            # FIXME: make messages idempotent (prevent duplicate processing)

            if not message.topic:
                continue

            topics = list(self._handlers.keys())

            for topic in topics:
                if fnmatch.fnmatch(message.topic, topic):
                    for handler in self._handlers[topic]:
                        await handler.chan.send(message)

            for topic in topics:
                if len(self._handlers[topic]) == 0:
                    del self._handlers[topic]

    async def close(self):
        """Disconnect from the gossip network and stop receiving messages."""
        handlers = [h for h in itertools.chain(*self._handlers.values())]
        await asyncio.gather(*[h.cancel() for h in handlers], return_exceptions=True)
        await self.gossip.close()

    def subscribe(self, topic, func):
        """Subscribe to a topic and register a handler."""
        handler = Handler(topic, func, loop=self._loop)
        self._handlers[topic].append(handler)
        return handler

    async def unsubscribe(self, handler):
        """Unsubscribe from a topic and unregister a handler."""
        await handler.cancel()
        self._handlers[handler.topic].remove(handler)

    async def publish(self, topic, message, peer_ids=None):
        """Publish a message to a topic."""
        # FIXME: make messages idempotent (prevent duplicate processing)
        # FIXME: allow sending to specific nodes
        message.topic = topic

        if peer_ids:
            for peer_id in peer_ids:
                if peer_id in self.gossip.topology:
                    await self.gossip.send(message, peer_id)
                else:
                    raise ValueError(f"Unknown node: {peer_id}")
        else:
            await self.gossip.send_gossip(message)

        return self._recv(topic, peer_ids=peer_ids)

    async def _recv(self, topic, peer_ids=None):
        chan = Channel(loop=self._loop)
        handler = self.subscribe(topic, chan.send)

        acks = set()
        if peer_ids:
            acks.update(peer_ids)

        try:
            async with asyncio.timeout(self.TIMEOUT):
                while True:
                    message = await chan.recv()
                    if message.metadata.ack:
                        acks.add(message.metadata.ack)
                        yield message

                    elif message.metadata.src in acks:
                        acks.remove(message.metadata.src)
                        yield message

                    else:
                        raise ValueError(f"Unknown message: {message}")

        except asyncio.TimeoutError:
            pass
        finally:
            await self.unsubscribe(handler)
            await chan.close()
