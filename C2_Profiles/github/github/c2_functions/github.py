from mythic_container.C2ProfileBase import *
from pathlib import Path

class Github(C2Profile):
    name = "github"
    description = "Github C2 Profilfe"
    author = "@scottctaylor12"
    is_p2p = False
    is_server_routed = False
    server_folder_path = Path(".") / "github" / "c2_code"
    server_binary_path = server_folder_path / "server.py"
    parameters = [
        C2ProfileParameter(
            name="github_repo",
            description="GitHub repository to send communication through",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="github_username",
            description="GitHub Username that owns the github_repo",
            default_value="",
            required=True,
        ),
        C2ProfileParameter(
            name="personal_access_token",
            description="GitHub Personal Access Token used to programatically access GitHub",
            default_value="github_pat_XXXXXX",
            required=True,
        ),
        C2ProfileParameter(
            name="server_issue_number",
            description="GitHub issue # that Mythic will post jobs to",
            default_value="1",
            required=True,
        ),
        C2ProfileParameter(
            name="client_issue_number",
            description="GitHub issue # that agents will post results to",
            default_value="2",
            required=True,
        ),
        C2ProfileParameter(
            name="callback_interval",
            description="Callback Interval in seconds",
            default_value="60",
            verifier_regex="^[0-9]+$",
            required=False,
        ),
        C2ProfileParameter(
            name="callback_jitter",
            description="Callback Jitter in percent",
            default_value="10",
            verifier_regex="^[0-9]+$",
            required=False,
        ),
        C2ProfileParameter(
            name="encrypted_exchange_check",
            description="Perform Key Exchange",
            choices=["T", "F"],
            parameter_type=ParameterType.ChooseOne,
            required=False,
        ),
        C2ProfileParameter(
            name="AESPSK",
            description="Crypto type",
            default_value="aes256_hmac",
            parameter_type=ParameterType.ChooseOne,
            choices=["aes256_hmac", "none"],
            required=False,
            crypto_type=True
        ),
        C2ProfileParameter(
            name="user_agent",
            description="User Agent",
            default_value="Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
            required=False,
        ),
        C2ProfileParameter(
            name="proxy_host",
            description="Proxy Host",
            default_value="",
            required=False,
            verifier_regex="^$|^(http|https):\/\/[a-zA-Z0-9]+",
        ),
        C2ProfileParameter(
            name="proxy_port",
            description="Proxy Port",
            default_value="",
            verifier_regex="^$|^[0-9]+$",
            required=False,
        ),
        C2ProfileParameter(
            name="proxy_user",
            description="Proxy Username",
            default_value="",
            required=False,
        ),
        C2ProfileParameter(
            name="proxy_pass",
            description="Proxy Password",
            default_value="",
            required=False,
        ),
        C2ProfileParameter(
            name="killdate",
            description="Kill Date",
            parameter_type=ParameterType.Date,
            default_value=365,
            required=False,
        ),
    ]