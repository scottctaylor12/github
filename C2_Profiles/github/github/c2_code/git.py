import aiohttp
from config import config
from mythic_container.logging import logger


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

async def post_comment(msg):
    print("CONFIG: " + str(config))
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
