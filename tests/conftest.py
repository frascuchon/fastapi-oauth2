import importlib
import os

import pytest
import social_core.backends as backends
from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from social_core.backends.github import GithubOAuth2
from social_core.backends.oauth import BaseOAuth2
from starlette.responses import RedirectResponse
from starlette.responses import Response

from fastapi_oauth2.client import OAuth2Client
from fastapi_oauth2.middleware import OAuth2Middleware
from fastapi_oauth2.security import OAuth2
from tests.idp import TestOAuth2
from tests.idp import get_idp

package_path = backends.__path__[0]


@pytest.fixture
def backends():
    backend_instances = []
    for module in os.listdir(package_path):
        try:
            module_instance = importlib.import_module("social_core.backends.%s" % module[:-3])
            backend_instances.extend([
                attr for attr in module_instance.__dict__.values()
                if type(attr) is type and all([
                    issubclass(attr, BaseOAuth2),
                    attr is not BaseOAuth2,
                ])
            ])
        except ImportError:
            continue
    return backend_instances


@pytest.fixture
def get_app():
    def fixture_wrapper(authentication: OAuth2 = None):
        if not authentication:
            authentication = OAuth2()

        oauth2 = authentication
        application = FastAPI()
        app_router = APIRouter()

        @app_router.get("/oauth2/{provider}/auth")
        async def login(request: Request, provider: str):
            return await request.auth.clients[provider].login_redirect(request)

        @app_router.get("/oauth2/{provider}/token")
        async def token(request: Request, provider: str):
            return await request.auth.clients[provider].token_redirect(request, app=get_idp())

        @app_router.get("/oauth2/logout")
        def logout(request: Request):
            response = RedirectResponse(request.base_url)
            response.delete_cookie("Authorization")
            return response

        @app_router.get("/user")
        def user(request: Request, _: str = Depends(oauth2)):
            return request.user

        @app_router.get("/auth")
        def auth(request: Request):
            access_token = request.auth.jwt_create({
                "id": 54321,
                "followers": 80,
                "sub": "1234567890",
                "name": "John Doe",
                "provider": "github",
                "emails": ["john.doe@test.py"],
                "image": "https://example.com/john.doe.png",
            })
            response = Response()
            response.set_cookie(
                "Authorization",
                value=f"Bearer {access_token}",
                max_age=request.auth.expires,
                expires=request.auth.expires,
                httponly=request.auth.http,
            )
            return response

        application.include_router(app_router)
        application.mount("", get_idp())
        application.add_middleware(OAuth2Middleware, config={
            "allow_http": True,
            "clients": [
                OAuth2Client(
                    backend=TestOAuth2,
                    client_id="test_id",
                    client_secret="test_secret",
                ),
                OAuth2Client(
                    backend=GithubOAuth2,
                    client_id="test_id",
                    client_secret="test_secret",
                ),
            ],
        })

        return application

    return fixture_wrapper
