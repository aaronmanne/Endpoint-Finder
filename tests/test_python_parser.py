"""
Unit tests for the Python parser.
"""

import unittest
from endpoint_finder.parsers.python import PythonParser


class TestPythonParser(unittest.TestCase):
    """Test cases for the Python parser."""
    
    def setUp(self):
        """Set up the test case."""
        self.parser = PythonParser()
    
    def test_flask_route_detection(self):
        """Test detection of Flask routes."""
        flask_code = """
from flask import Flask

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    \"\"\"Get all users.\"\"\"
    return {'users': []}

@app.route('/api/users/<int:user_id>', methods=['GET', 'POST'])
def get_user(user_id):
    return {'user': user_id}

@app.get('/api/items')
def get_items():
    return {'items': []}

@app.post('/api/items')
def create_item():
    return {'status': 'created'}
"""
        
        endpoints = self.parser.parse(flask_code, 'app.py')
        
        # Check that we found 5 endpoints (2 for the first route with GET and POST methods,
        # 1 for the second route with GET method, and 2 for the app.get and app.post routes)
        self.assertEqual(len(endpoints), 5)
        
        # Check that the endpoints have the correct paths and methods
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/api/users', 'GET'),
            ('/api/users/<int:user_id>', 'GET'),
            ('/api/users/<int:user_id>', 'POST'),
            ('/api/items', 'GET'),
            ('/api/items', 'POST')
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Flask')
    
    def test_django_url_detection(self):
        """Test detection of Django URL patterns."""
        django_code = """
from django.urls import path
from . import views

urlpatterns = [
    path('api/users/', views.user_list, name='user-list'),
    path('api/users/<int:pk>/', views.user_detail, name='user-detail'),
    path('api/groups/', views.group_list, name='group-list'),
]
"""
        
        endpoints = self.parser.parse(django_code, 'urls.py')
        
        # Check that we found 3 endpoints
        self.assertEqual(len(endpoints), 3)
        
        # Check that the endpoints have the correct paths
        paths = {endpoint['path'] for endpoint in endpoints}
        expected_paths = {
            'api/users/',
            'api/users/<int:pk>/',
            'api/groups/'
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Django')
    
    def test_fastapi_route_detection(self):
        """Test detection of FastAPI routes."""
        fastapi_code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/users")
async def get_users():
    \"\"\"Get all users.\"\"\"
    return {"users": []}

@app.post("/api/users")
async def create_user():
    return {"status": "created"}

@app.put("/api/users/{user_id}")
async def update_user(user_id: int):
    return {"user": user_id, "status": "updated"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    return {"status": "deleted"}
"""
        
        endpoints = self.parser.parse(fastapi_code, 'main.py')
        
        # Check that we found 4 endpoints
        self.assertEqual(len(endpoints), 4)
        
        # Check that the endpoints have the correct paths and methods
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/api/users', 'GET'),
            ('/api/users', 'POST'),
            ('/api/users/{user_id}', 'PUT'),
            ('/api/users/{user_id}', 'DELETE')
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'FastAPI')


if __name__ == '__main__':
    unittest.main()