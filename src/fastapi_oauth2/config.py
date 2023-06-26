import os
from typing import List

from .client import OAuth2Client


class OAuth2Config:
    allow_http: bool
    jwt_secret: str
    jwt_expires: int
    jwt_algorithm: str
    clients: List[OAuth2Client]

    def __init__(
            self,
            *,
            allow_http: bool = False,
            jwt_secret: str = "",
            jwt_expires: int = 900,
            jwt_algorithm: str = "HS256",
            clients: List[OAuth2Client] = None,
    ):
        if allow_http:
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        self.allow_http = allow_http
        self.jwt_secret = jwt_secret
        self.jwt_expires = int(jwt_expires)
        self.jwt_algorithm = jwt_algorithm
        self.clients = clients or []
