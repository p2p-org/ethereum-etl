import asyncio
import logging
from websockets import connect


class WssBlockListener:
    """
    Listens for new block events via a WebSocket connection.
    """

    def __init__(self, wss_uri) -> None:
        """
        Initializes the listener with the WebSocket URI.

        Args:
            wss_uri (str): The WebSocket URI to connect to.
        """
        self.logger = logging.getLogger("CompositeItemExporter")
        self.wss_uri = wss_uri
        self.subscribed = False

    async def subscribe(self) -> None:
        """
        Subscribes to new block events.
        """
        self.new_block_lock = asyncio.Condition()
        self.subscribed = True
        async with connect(self.wss_uri) as ws:
            await ws.send(
                '{"id": 1, "method": "eth_subscribe", "params": ["newHeads"]}'
            )
            subscription_response = await ws.recv()
            self.logger.debug("Subscription acquired %s", subscription_response)
            while self.subscribed:
                await asyncio.wait_for(ws.recv(), timeout=60)
                async with self.new_block_lock:
                    self.new_block_lock.notify_all()

    async def wait_for_new_block(self) -> None:
        async with self.new_block_lock:
            await self.new_block_lock.wait()

    def close(self) -> None:
        """
        Closes the listener and unsubscribes.
        """
        self.subscribed = False
