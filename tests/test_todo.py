from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from todo import app, get_db, ToDo, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DIR = Path(__file__).parent
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DIR}/todo.test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_module(module):
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_db():
    db = Session(bind=engine)
    yield db
    db.query(ToDo).delete()
    db.commit()


def test_create_todo(test_db):
    client = TestClient(app)

    # Create new todo
    new_todo = {"title": "Test Todo"}
    response = client.post("/todos", json=new_todo)
    assert response.status_code == 200

    todo = response.json()
    assert todo["title"] == new_todo["title"]
    assert todo["completed"] == False
    assert todo["id"] is not None


def test_read_todos(test_db):
    client = TestClient(app)

    # Create some test todos
    new_todos = [
        {"title": "Todo 1"},
        {"title": "Todo 2"},
        {"title": "Todo 3"}
    ]
    for todo in new_todos:
        client.post("/todos", json=todo)

    # Get all todos
    response = client.get("/todos")
    assert response.status_code == 200

    todos = response.json()
    assert len(todos) >= len(new_todos)
    for i, todo in enumerate(new_todos):
        assert todos[i]["title"] == todo["title"]
        assert todos[i]["completed"] == False
        assert todos[i]["id"] is not None


def test_read_todo(test_db):
    client = TestClient(app)

    # Create new todo
    new_todo = {"title": "Test Todo"}
    response = client.post("/todos", json=new_todo)
    assert response.status_code == 200

    todo = response.json()
    assert todo["title"] == new_todo["title"]
    assert todo["completed"] == False
    assert todo["id"] is not None

    # Get the todo by id
    response = client.get(f"/todos/{todo['id']}")
    assert response.status_code == 200

    retrieved_todo = response.json()
    assert retrieved_todo == todo


def test_update_todo(test_db):
    client = TestClient(app)

    # Create new todo
    new_todo = {"title": "Test Todo"}
    response = client.post("/todos", json=new_todo)
    assert response.status_code == 200

    todo = response.json()
    assert todo["title"] == new_todo["title"]
    assert todo["completed"] == False
    assert todo["id"] is not None

    # Update the todo
    updated_todo = {"title": "Updated Test Todo", "completed": True}
    response = client.put(f"/todos/{todo['id']}", json=updated_todo)
    assert response.status_code == 200

    todo = response.json()
    assert todo["title"] == updated_todo["title"]
    assert todo["completed"] == updated_todo["completed"]
    assert todo["id"] is not None

    # Get the updated todo
    response = client.get(f"/todos/{todo['id']}")
    assert response.status_code == 200

    retrieved_todo = response.json()
    assert retrieved_todo == todo


def test_delete_todo(test_db):
    # Create a todo
    todo_data = {"title": "Test Todo"}
    response = TestClient(app).post("/todos", json=todo_data)
    todo_id = response.json()["id"]

    # Delete the todo
    response = TestClient(app).delete(f"/todos/{todo_id}")

    assert response.status_code == 200

    # Make sure the todo was deleted
    response = TestClient(app).get(f"/todos/{todo_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}
