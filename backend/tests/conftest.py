import os
import sys
import tempfile

# 在导入 app 之前覆盖环境：测试使用独立的 SQLite 数据库与 Mock 模式
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp(prefix='ews-test-')}/test.db"
os.environ["ASSEMBLYAI_API_KEY"] = ""
os.environ["DEMO_MODE"] = "false"

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture()
def app():
    app = create_app()
    with app.app_context():
        yield app
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


def make_user(username: str, role: str, password: str = "123456") -> User:
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username: str, password: str = "123456") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["data"]["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
