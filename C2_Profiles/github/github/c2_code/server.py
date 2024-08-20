#!/usr/local/bin/python
import hashlib
import hmac
import json
import logging
import os
import requests
import sys

from flask import Flask, request, jsonify

config = {}

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
        print("Comment successfully created.")
        return response.json()  # Return the JSON response with comment details
    else:
        print(f"Failed to create comment. Status code: {response.status_code}")
        print(f"Response: {response.text}")
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
        print(f"Comment {comment_id} successfully deleted.")
        print()
    else:
        print(f"Failed to delete comment {comment_id}. Status code: {response.status_code}")
        print(f"Response: {response.text}")

@app.route('/', methods=['POST'])
def github_webhook():
    # Verify the signature to ensure the request is from GitHub
    signature = request.headers.get('X-Hub-Signature-256')
    if signature is None:
        print("basic web request with no signature")
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

if __name__ == "__main__":
    print('Loading configuration')
    config_file = open("config.json", 'rb')
    config = json.loads(config_file.read().decode('utf-8'))
    config['mythic_address'] = os.environ['MYTHIC_ADDRESS']
    sys.stdout.flush()
    print(f"Starting web server at 0.0.0.0:{config['port']}")
    app.run(host='0.0.0.0', port=config['port'])