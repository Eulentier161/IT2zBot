import time
from pathlib import Path

import httpx
import jwt
import yaml
from cryptography.hazmat.primitives import serialization


def get_config():
    with open(Path(__file__, "../../config.yaml").resolve()) as f:
        return yaml.safe_load(f)


def _get_jwt() -> str:
    """returns a jwt to authenticate against the github api"""
    t = time.time()
    payload = {
        "iat": int(t - 60),
        "exp": int(t + (10 * 60)),
        "iss": get_config()["gh_app_id"],
    }
    private_key = Path(__file__, "../../gh_privkey.pem").resolve()
    private_key = serialization.load_pem_private_key(private_key.read_bytes(), None)
    return jwt.encode(payload, private_key, "RS256")


def get_access_token() -> dict:
    return httpx.post(
        f"https://api.github.com/app/installations/{get_config()['gh_installation_id']}/access_tokens",
        headers={"Authorization": f"Bearer {_get_jwt()}"},
    ).json()["token"]
