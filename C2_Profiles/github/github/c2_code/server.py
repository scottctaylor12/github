#!/usr/local/bin/python
import hashlib
import hmac
import json
import logging
import os
import sys
import asyncio
import aiohttp
from mythic_container.logging import logger
from quart import Quart, request, jsonify


config = {}


app = Quart(__name__)

# turn off standard Quart logging
log = logging.getLogger('quart.app')
log.setLevel(logging.ERROR)

def verify_signature(payload, signature, secret):
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest('sha256=' + mac.hexdigest(), signature)

async def post_comment(msg):
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/{config['server_issue']}/comments"
    payload = {
        'body': msg
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers={
            'Authorization': f'token {config["github_token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }, json=payload) as response:
            if response.status == 201:
                logger.info("Comment successfully created.")
                return await response.json()
            else:
                logger.info(f"Failed to create comment. Status code: {response.status}")
                logger.info(f"Response: {await response.text()}")
                return None

async def delete_comment(comment_id):
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/issues/comments/{comment_id}"

    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers={
            'Authorization': f'token {config["github_token"]}',
            'Accept': 'application/vnd.github.v3+json'
        }) as response:
            if response.status == 204:
                logger.info(f"Comment {comment_id} successfully deleted.")
            else:
                logger.info(f"Failed to delete comment {comment_id}. Status code: {response.status}")
                logger.info(f"Response: {await response.text()}")

@app.route('/', methods=['POST'])
async def github_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        logger.info("Basic web request with no signature")
        return jsonify({'error': 'Missing signature'}), 400
    if not verify_signature(await request.data, signature, config['webhook_secret']):
        return jsonify({'error': 'Invalid signature'}), 400

    event = request.headers.get('X-GitHub-Event')
    payload = await request.json

    if event == 'issue_comment':
        action = payload['action']
        issue = payload['issue']
        comment = payload['comment']

        if action == 'created' and issue['number'] == config['client_issue']:
            async with aiohttp.ClientSession() as session:
                async with session.post(config['mythic_address'], headers={"Mythic": "github"}, data=comment['body']) as resp:
                    response_text = await resp.text()
                    await post_comment(response_text)
                    await delete_comment(comment['id'])

    return jsonify({'status': 'success'}), 200

async def main():
    global config
    logger.info('Loading configuration')
    with open("config.json", 'rb') as config_file:
        config = json.loads(config_file.read().decode('utf-8'))
    config['mythic_address'] = os.environ['MYTHIC_ADDRESS']
    sys.stdout.flush()
    logger.info(f"Starting web server at 0.0.0.0:{config['port']}")
    await app.run_task(host='0.0.0.0', port=config['port'])

asyncio.run(main())