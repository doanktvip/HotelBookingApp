import pytest
from app import create_app
from app.extensions import db
import threading
import time
from werkzeug.serving import make_server
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from tests.fixtures_db import *

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
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

@pytest.fixture(scope='function')
def test_client(test_app, test_db):
    return test_app.test_client()

@pytest.fixture(scope='function')
def client(test_client):
    return test_client

@pytest.fixture(scope='function')
def test_session(test_db):

    # Sử dụng trực tiếp db.session để dữ liệu thực sự được commit xuống file test.db
    yield test_db.session

   
    # Dọn dẹp dữ liệu sau mỗi test để các test không ảnh hưởng lẫn nhau
    test_db.session.remove()
    for table in reversed(test_db.metadata.sorted_tables):
        test_db.session.execute(table.delete())
    test_db.session.commit()

@pytest.fixture(scope="function")
def selenium_driver():
    """
    Selenium WebDriver fixture for E2E/UI testing.
    Runs in normal UI mode (headless removed).
    """
    
    options = Options()
    # options.add_argument('--headless') # Đã tắt chế độ headless để xem UI
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    # Initialize WebDriver
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    
    yield driver

    
    driver.quit()


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    import shutil
    screenshots_dir = "screenshots"
    if os.path.exists(screenshots_dir):
        shutil.rmtree(screenshots_dir)
    os.makedirs(screenshots_dir, exist_ok=True)


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', port, app, threaded=True)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.ctx.pop()

@pytest.fixture(scope="session")
def live_server(app):
    """ Custom live_server using threading to avoid multiprocessing bugs """
    server = ServerThread(app, 5001)
    server.start()
    time.sleep(1) # Chờ server khởi động
    
    class LiveServerInfo:
        url = "http://127.0.0.1:5001"
        def __init__(self, app):
            self.app = app
        
    yield LiveServerInfo(app)
    server.shutdown()
    server.join()
