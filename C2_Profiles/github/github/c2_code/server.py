#!/usr/local/bin/python
import asyncio
import hashlib
import hmac
import json
import logging
import os
import requests
import sys
import threading
import uuid
import websockets

import grpc.aio
from flask import Flask, request, jsonify
from mythic_container.grpc.pushC2GRPC_pb2_grpc import PushC2Stub
from mythic_container.grpc import pushC2GRPC_pb2 as grpcFuncs
from mythic_container.logging import logger

config = {}
UUIDToWebsocketConn = {}
grpcStream = None

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def verify_signature(payload, signature, secret):
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)

def post_comment(msg):
    # GitHub API endpoint for creating an issue comment
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/{config['server_issue']}/comments"

    # The payload containing the comment body
    payload = {
        'body': msg
    }

    # Perform the POST request
    response = requests.post(url, 
                             headers={
                                'Authorization': f'token {config["github_token"]}',
                                'Accept': 'application/vnd.github.v3+json'
                             }, 
                             json=payload)

    if response.status_code == 201:
        logger.info("Comment successfully created.")
        return response.json()  # Return the JSON response with comment details
    else:
        logger.info(f"Failed to create comment. Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")
        return None
    
def delete_comment(comment_id):
    # GitHub API endpoint for deleting an issue comment
    #url = f'{URL}/comments/{comment_id}'
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/comments/{comment_id}"
    # Perform the DELETE request
    response = requests.delete(url, 
                               headers= {
                                'Authorization': f'token {config["github_token"]}',
                                'Accept': 'application/vnd.github.v3+json'
                                }
                              )

    if response.status_code == 204:
        logger.info(f"Comment {comment_id} successfully deleted.")
        logger.info()
    else:
        logger.info(f"Failed to delete comment {comment_id}. Status code: {response.status_code}")
        logger.info(f"Response: {response.text}")

@app.route('/', methods=['POST'])
def github_webhook():
    # Verify the signature to ensure the request is from GitHub
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        logger.info("basic web request with no signature")
        return jsonify({'error': 'Missing signature'}), 400
    if not verify_signature(request.data, signature, config['webhook_secret']):
        return jsonify({'error': 'Invalid signature'}), 400
    # Process the GitHub event
    event = request.headers.get('X-GitHub-Event')
    payload = request.json
    if event == 'issue_comment':
        action = payload['action']
        issue = payload['issue']
        comment = payload['comment']
        
        if action == 'created' and issue['number'] == config['client_issue']:
            # Send message to Mythic
            resp = requests.post(
                config['mythic_address'],
                headers={"Mythic": "github"},
                data=comment['body']
                )
            # Post Mythic reponse to Github
            post_comment(resp.text)
            delete_comment(comment['id'])

    return jsonify({'status': 'success'}), 200

async def handleStreamConnection(client):
    global UUIDToWebsocketConn
    global grpcStream
    try:
        while True:
            grpcStream = client.StartPushC2StreamingOneToMany()
            await grpcStream.write(grpcFuncs.PushC2MessageFromAgent(
                C2ProfileName="github"
            ))
            logger.info(f"Connected to gRPC for pushC2 StreamingOneToMany")
            async for request in grpcStream:
                # this is streaming responses from Mythic to go to agents
                try:
                    if request.TrackingID in UUIDToWebsocketConn:
                        logger.info(f"sending message back to websocket for id: {request.TrackingID}")
                        await UUIDToWebsocketConn[request.TrackingID].send(json.dumps({"data": request.Message.decode()}))
                    else:
                        logger.error(f"tracking ID not tracked: {request.TrackingID} ")
                except Exception as d:
                    logger.exception(f"Failed to process handleStreamConnection message:\n{d}")

            logger.error(f"disconnected from gRPC for handleStreamConnection")
    except Exception as e:
        logger.exception(f"[-] exception in handleStreamConnection: {e}")


async def handle_connection(websocketConn: websockets.WebSocketServerProtocol):
    global UUIDToWebsocketConn
    global grpcStream
    connUUID = str(uuid.uuid4())
    logger.info(f"New tracking ID created: {connUUID}")
    UUIDToWebsocketConn[connUUID] = websocketConn
    try:
        async for message in websocketConn:
            # get message from agent and send it to grpc stream
            logger.info(f"new websocket msg for id: {connUUID}")
            while True:
                if grpcStream is None:
                    await asyncio.sleep(1)
                    continue
                break
            try:
                jsonMsg = json.loads(message)
                await grpcStream.write(grpcFuncs.PushC2MessageFromAgent(
                    C2ProfileName="github",
                    RemoteIP=str(websocketConn.remote_address),
                    Base64Message=jsonMsg["data"].encode("utf-8"),
                    TrackingID=connUUID
                ))
            except Exception as e:
                logger.info(f"Hit exception trying to send websocket message to grpc: {e}")
                await asyncio.sleep(1)
    except Exception as c:
        if grpcStream is not None:
            logger.info(f"websocket connection dead, removing it: {connUUID}")
            try:
                del UUIDToWebsocketConn[connUUID]
                await grpcStream.write(grpcFuncs.PushC2MessageFromAgent(
                    C2ProfileName="github",
                    RemoteIP=str(websocketConn.remote_address),
                    TrackingID=connUUID,
                    AgentDisconnected=True
                ))
            except Exception as e:
                logger.error(f"Failed to send message to Mythic that connection dropped: {e}")

async def handleGrpcStreamingServices():
    maxInt = 2 ** 31 - 1
    while True:
        try:
            logger.info(f"Attempting connection to gRPC for pushC2OneToMany...")
            channel = grpc.aio.insecure_channel(
                f'127.0.0.1:17444',
                options=[
                    ('grpc.max_send_message_length', maxInt),
                    ('grpc.max_receive_message_length', maxInt),
                ])
            await channel.channel_ready()
            client = PushC2Stub(channel=channel)
            streamConnections = handleStreamConnection(client)
            logger.info(f"[+] Successfully connected to gRPC for pushC2OneToMany")
            await asyncio.gather(streamConnections)
        except Exception as e:
            logger.exception(f"Translation gRPC services closed for pushC2OneToMany: {e}")

if __name__ == "__main__":
    logger.info('Loading configuration')
    config_file = open("config.json", 'rb')
    config = json.loads(config_file.read().decode('utf-8'))
    config['mythic_address'] = os.environ['MYTHIC_ADDRESS']
    sys.stdout.flush()
    logger.info(f"Starting flask server at 0.0.0.0:{config['port']}")
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=config['port']))
    flask_thread.start()

    logger.info("starting grpc connection server")
    asyncio.create_task(handleGrpcStreamingServices())