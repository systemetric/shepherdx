import asyncio
from shepherdx.common.mqtt import ShepherdMqtt, MqttMessage
from dataclasses import dataclass

@dataclass
class CountMessage:
    num: int

async def main():
    async with ShepherdMqtt("test_service") as client:
        async def on_count(msg: CountMessage):
            print(f"Count: {msg.num}")

        await client.subscribe("count", on_count, CountMessage)

        i = 0
        while True:
            await client.publish("count", CountMessage(num=i))
            i += 1

            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
