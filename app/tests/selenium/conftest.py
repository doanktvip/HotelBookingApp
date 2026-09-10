import sys
import os

# Đảm bảo thư mục gốc dự án có trong sys.path (3 cấp từ app/tests/selenium lên root)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import threading
import time
import pytest
from werkzeug.serving import make_server
from app import create_app
from app.extensions import db
from app import models


@pytest.fixture(scope='session')
def app():
    app_instance = create_app('testing')
    with app_instance.app_context():
        yield app_instance


@pytest.fixture(scope='session')
def test_app(app):
    return app


@pytest.fixture(scope='session')
def test_db(test_app):
    with test_app.app_context():
        from app import models
        db.create_all()
        yield db
        db.session.remove()


@pytest.fixture(scope='function')
def test_session(test_db):
    yield test_db.session
    test_db.session.remove()


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        super().__init__()
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.ctx.pop()


@pytest.fixture(scope="session")
def live_server(app, test_db):
    port = 5001
    server = ServerThread(app, port)
    server.start()
    time.sleep(1)

    class LiveServerInfo:
        url = f"http://127.0.0.1:{port}"

        def __init__(self, app):
            self.app = app

    yield LiveServerInfo(app)
    server.shutdown()
    server.join(timeout=3)
