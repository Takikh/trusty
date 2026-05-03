import asyncio
import websockets
import json

async def test():
    try:
        async with websockets.connect('ws://localhost:8001/ws/interview/test_doctor') as ws:
            await ws.send('START')
            while True:
                msg = await ws.recv()
                if isinstance(msg, bytes):
                    print(f"Received audio bytes: {len(msg)}")
                else:
                    print(f"Received msg: {msg}")
    except Exception as e:
        print(f"Exception: {e}")

asyncio.run(test())
