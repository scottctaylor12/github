import asyncio
import github_client as github_client
import grpc.aio
import json
from config import config
from mythic_container.grpc.pushC2GRPC_pb2_grpc import PushC2Stub
from mythic_container.grpc import pushC2GRPC_pb2 as grpcFuncs
from mythic_container.logging import logger


grpcStream = None


# connect to Mythic gRPC endpoint
async def handleGrpcStreamingServices():
    maxInt = 2**31 - 1
    while True:
        try:
            logger.info(f"Attempting connection to gRPC for pushC2OneToMany...")
            channel = grpc.aio.insecure_channel(
                f"127.0.0.1:17444",
                options=[
                    ("grpc.max_send_message_length", maxInt),
                    ("grpc.max_receive_message_length", maxInt),
                ],
            )
            await channel.channel_ready()
            client = PushC2Stub(channel=channel)
            streamConnections = handleStreamConnection(client)
            logger.info(f"[+] Successfully connected to gRPC for pushC2OneToMany")
            await asyncio.gather(streamConnections)
        except Exception as e:
            logger.exception(
                f"Translation gRPC services closed for pushC2OneToMany: {e}"
            )


# Receive messages from Mythic and post to GitHub
async def handleStreamConnection(client):
    global grpcStream
    try:
        while True:
            grpcStream = client.StartPushC2StreamingOneToMany()
            await grpcStream.write(
                grpcFuncs.PushC2MessageFromAgent(C2ProfileName="github")
            )
            logger.info(f"Connected to gRPC for pushC2 StreamingOneToMany")
            async for request in grpcStream:
                # this is streaming responses from Mythic to go to agents
                try:
                    logger.info("posting message to github")
                    await github_client.post_comment(request.Message.decode())
                except Exception as d:
                    logger.exception(
                        f"Failed to process handleStreamConnection message:\n{d}"
                    )

            logger.error(f"disconnected from gRPC for handleStreamConnection")
    except Exception as e:
        logger.exception(f"[-] exception in handleStreamConnection: {e}")


# Receive base64 message from agent and send to Mythic
async def send_to_mythic(msg):
    global grpcStream
    logger.info("Sending message from GitHub to Mythic...")
    while True:
        if grpcStream is None:
            await asyncio.sleep(1)
            continue
        break
    await grpcStream.write(
        grpcFuncs.PushC2MessageFromAgent(
            C2ProfileName="github",
            Base64Message=msg.encode("ascii"),
        )
    )
