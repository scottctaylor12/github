#!/usr/local/bin/python
import aiohttp
import asyncio
import github_client as github_client
import hashlib
import hmac
import json
import logging
import mythic_client as mythic_client
import os
import sys
from config import config
from mythic_container.logging import logger
from quart import Quart, request, jsonify


app = Quart(__name__)

log = logging.getLogger('quart.app')
log.setLevel(logging.INFO)

def verify_signature(payload, signature, secret):
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)

@app.route('/', methods=['POST'])
async def github_webhook():
    # Verify request came from intended GitHub Webhook
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        logger.info("Basic web request with no signature")
        return jsonify({'error': 'Missing signature'}), 400
    if not verify_signature(await request.data, signature, config['webhook_secret']):
        return jsonify({'error': 'Invalid signature'}), 400

    # Process GitHub Webhook message
    event = request.headers.get('X-GitHub-Event')
    payload = await request.json
    if event == 'issue_comment':
        action = payload['action']
        issue = payload['issue']
        comment = payload['comment']

        if action == 'created' and issue['number'] == config['client_issue']:
            await mythic_client.send_to_mythic(comment['body'])
            await github_client.delete_comment(comment['id'])

    return jsonify({'status': 'success'}), 200

async def main():
    # Load configuration
    global config
    logger.info('Loading configuration')
    with open("config.json", 'rb') as config_file:
        config.update(json.loads(config_file.read().decode('utf-8')))
    config['mythic_address'] = os.environ['MYTHIC_ADDRESS']
    sys.stdout.flush()

    # Connect to Mythic gRPC server
    asyncio.create_task(mythic_client.handleGrpcStreamingServices())

    # Start Quart server to receive GitHub webhook messages 
    logger.info(f"Starting web server at 0.0.0.0:{config['port']}")
    await app.run_task(host='0.0.0.0', port=config['port'])

asyncio.run(main())