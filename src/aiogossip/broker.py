import asyncio
import collections
import fnmatch
import itertools

from .concurrency import Channel, TaskManager
from .gossip import Gossip
from .types_pb2 import Message


class Handler:
    def __init__(self, topic, func, loop: asyncio.AbstractEventLoop):
        self._loop = loop

        self.topic = topic
        self.func = func

        self.chan = Channel(loop=self._loop)
        self.task_manager = TaskManager(loop=self._loop)
        self.task_manager.create_task(self())

        self.hooks = []

    async def __call__(self):
        while True:
            message = await self.chan.recv()
            result = await self.func(message)

            if result is None:
                continue

            for hook in self.hooks:
                self.task_manager.create_task(hook(message, result))

    def hook(self, func):
        self.hooks.append(func)

    async def cancel(self):
        await self.chan.close()
        await self.task_manager.close()


class Broker:
    TIMEOUT = 1

    def __init__(self, gossip: Gossip, loop: asyncio.AbstractEventLoop = None):
        """
        Initialize a Broker instance.

        Args:
            gossip (Gossip): The Gossip instance used for communication.
            loop (asyncio.AbstractEventLoop, optional): The event loop to use.
        """
        self._loop = loop or gossip.transport._loop

        self.gossip = gossip
        self.handlers = collections.defaultdict(list)

    async def close(self):
        """
        Disconnect from the gossip network and stop receiving messages.
        """
        handlers = [h for h in itertools.chain(*self.handlers.values())]
        await asyncio.gather(*[h.cancel() for h in handlers], return_exceptions=True)
        await self.gossip.close()

    async def listen(self):
        """
        Connect to the gossip network and start receiving messages.
        """
        async for message in self.gossip.recv():
            # FIXME: make messages idempotent (prevent duplicate processing of gossip messages)
            handlers = list(self.handlers.keys())

            if f"recv:{message.id}" in handlers:
                for handler in self.handlers[f"recv:{message.id}"]:
                    await handler.chan.send(message)

            elif message.topic:
                for topic in handlers:
                    if fnmatch.fnmatch(message.topic, topic):
                        for handler in self.handlers[topic]:
                            await handler.chan.send(message)

            else:
                continue

            for topic in handlers:
                if len(self.handlers[topic]) == 0:
                    del self.handlers[topic]

    def subscribe(self, topic, func):
        """
        Subscribe to a topic and register a handler.

        Args:
            topic (str): The topic to subscribe to.
            func (callable): The handler function to be called when a message is received.

        Returns:
            Handler: The handler object associated with the subscription.
        """
        handler = Handler(topic, func, loop=self._loop)
        self.handlers[topic].append(handler)
        return handler

    async def unsubscribe(self, handler):
        """
        Unsubscribe from a topic and unregister a handler.

        Args:
            handler (Handler): The handler object to be unregistered.
        """
        await handler.cancel()
        self.handlers[handler.topic].remove(handler)

    async def publish(self, topic, message, peer_ids=None):
        """
        Publish a message to a topic.

        Args:
            topic (str): The topic to publish the message to.
            message (Message): The message to be published.
            peer_ids (list, optional):
                The list of peer IDs to send the message to.
                If not provided, the message will be sent to all nodes in the gossip network.

        Raises:
            ValueError: If the message ID is missing.
        """

        message.topic = topic
        if not message.id:
            raise ValueError("Message ID is required:", message)
        message_id = message.id

        if peer_ids:
            for peer_id in peer_ids:
                if peer_id in self.gossip.topology:
                    await self.gossip.send(message, peer_id)
                else:
                    raise ValueError(f"Unknown node: {peer_id}")
        else:
            await self.gossip.send_gossip(message)

        return self._recv(message_id, peer_ids=peer_ids)

    async def _recv(self, message_id, peer_ids=None):
        """
        Receive messages with the given message ID.

        Args:
            message_id (str): The message ID to filter the received messages.
            peer_ids (list, optional):
                The list of peer IDs to expect messages from.
                If not provided, the message will be sent to all nodes in the gossip network.

        Yields:
            Message: The received messages.
        """
        chan = Channel(loop=self._loop)
        handler = self.subscribe(f"recv:{message_id}", chan.send)

        acks = set()
        if peer_ids:
            acks.update(peer_ids)

        try:
            async with asyncio.timeout(self.TIMEOUT):
                while True:
                    message = await chan.recv()

                    if Message.Kind.ACK in message.kind:
                        acks.add(message.routing.snode)
                        yield message  # FIXME: don't yield acks

                    elif message.routing.snode in acks:
                        acks.remove(message.routing.snode)
                        yield message

                    else:
                        raise ValueError(f"Unknown message: {message}")

        except asyncio.TimeoutError:
            pass
        finally:
            await self.unsubscribe(handler)
            await chan.close()
