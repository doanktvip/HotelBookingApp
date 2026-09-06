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
def test_session(test_db):
    yield test_db.session
    
    test_db.session.remove()
    for table in reversed(test_db.metadata.sorted_tables):
        test_db.session.execute(table.delete())
    test_db.session.commit()

@pytest.fixture(scope="function")
def selenium_driver():
    options = Options()
    # options.add_argument('--headless') # Đã tắt chế độ headless để xem UI
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
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

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.passed:
        driver = item.funcargs.get("selenium_driver", None)
        if driver:
            os.makedirs("screenshots", exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            screenshot_path = f"screenshots/{item.name}_{timestamp}.png"
            driver.save_screenshot(screenshot_path)


class ServerThread(threading.Thread):
    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.ctx.pop()

@pytest.fixture(scope="session")
def live_server(app):
    server = ServerThread(app, 5001)
    server.start()
    time.sleep(1) 
    
    class LiveServerInfo:
        url = "http://127.0.0.1:5001"
        def __init__(self, app):
            self.app = app
        
    yield LiveServerInfo(app)
    server.shutdown()
    server.join()

