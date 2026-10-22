import pytest

import app as task_app
from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset task data and identifiers before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report", "priority": "Medium"},
        {"id": 2, "title": "Project-2 MMFs", "priority": "Medium"}
    ])
    task_app.next_id = 3


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """List all existing tasks with their priorities."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_with_priority(client, priority):
    """Create a task with each supported priority value."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    task = response.get_json()
    assert task['title'] == f"{priority} task"
    assert task['priority'] == priority


def test_add_task_defaults_to_medium_priority(client):
    """Default a task priority to Medium when it is omitted."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_empty_priority_defaults_to_medium(client):
    """Default an empty priority value to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Empty priority task", "priority": ""}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_rejects_invalid_priority(client):
    """Reject priorities outside the supported values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid task", "priority": "Urgent"}
    )

    assert response.status_code == 400
    assert 'error' in response.get_json()


@pytest.mark.parametrize('priority', [[], {}, 123, True])
def test_add_task_rejects_malformed_priority_types(client, priority):
    """Reject non-string priority values with a validation response."""
    response = client.post(
        '/api/tasks',
        json={"title": "Malformed priority task", "priority": priority}
    )

    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_add_task_success(client):
    """Create a task and retain existing creation behavior."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    assert response.get_json()['priority'] == 'Medium'

    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject task creation when the title is missing."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete an existing task while retaining the remaining tasks."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200

    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
    assert data[0]['priority'] == 'Medium'
