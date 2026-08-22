import pytest
from app import create_app
from app.extensions import db

@pytest.fixture(scope='session')
def test_app():
    app = create_app('testing')
    
    with app.app_context():
        yield app

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
    connection = test_db.engine.connect()
    transaction = connection.begin()
    
    from sqlalchemy.orm import scoped_session, sessionmaker
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    
    test_db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

# Import toàn bộ các Mock Data Fixtures từ file fixtures_db.py
from tests.fixtures_db import *
