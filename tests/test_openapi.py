"""
Tests for OpenAPI/Swagger functionality.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from endpoint_finder.openapi import (
    find_openapi_files,
    validate_openapi_file,
    generate_openapi_spec,
    save_generated_openapi
)


class TestOpenAPI(unittest.TestCase):
    """Test cases for OpenAPI/Swagger functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp(prefix="endpoint-finder-test-")
        
        # Create a sample OpenAPI file
        self.swagger_json_path = os.path.join(self.temp_dir, "swagger.json")
        self.swagger_json_content = {
            "swagger": "2.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/api/test": {
                    "get": {
                        "summary": "Test endpoint"
                    }
                }
            }
        }
        
        with open(self.swagger_json_path, 'w') as f:
            json.dump(self.swagger_json_content, f)
        
        # Create a sample OpenAPI 3.0 file
        self.openapi_yaml_path = os.path.join(self.temp_dir, "openapi.yaml")
        self.openapi_yaml_content = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /api/test:
    get:
      summary: Test endpoint
"""
        
        with open(self.openapi_yaml_path, 'w') as f:
            f.write(self.openapi_yaml_content)
        
        # Create a non-OpenAPI JSON file
        self.non_openapi_path = os.path.join(self.temp_dir, "config.json")
        with open(self.non_openapi_path, 'w') as f:
            f.write('{"config": "value"}')
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary files
        for file_path in [self.swagger_json_path, self.openapi_yaml_path, self.non_openapi_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Clean up output directory if it exists
        output_dir = os.path.join(self.temp_dir, "output")
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                os.remove(os.path.join(output_dir, file))
            os.rmdir(output_dir)
        
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_validate_openapi_file_swagger_json(self):
        """Test validating a Swagger 2.0 JSON file."""
        format_type, version, info = validate_openapi_file(self.swagger_json_path)
        
        self.assertEqual(format_type, "json")
        self.assertEqual(version, "Swagger 2.0")
        self.assertEqual(info["title"], "Test API")
        self.assertEqual(info["version"], "1.0.0")
    
    def test_validate_openapi_file_openapi_yaml(self):
        """Test validating an OpenAPI 3.0 YAML file."""
        format_type, version, info = validate_openapi_file(self.openapi_yaml_path)
        
        self.assertEqual(format_type, "yaml")
        self.assertEqual(version, "OpenAPI 3.0.0")
        self.assertEqual(info["title"], "Test API")
        self.assertEqual(info["version"], "1.0.0")
    
    def test_validate_openapi_file_non_openapi(self):
        """Test validating a non-OpenAPI file."""
        format_type, version, info = validate_openapi_file(self.non_openapi_path)
        
        self.assertIsNone(format_type)
        self.assertIsNone(version)
        self.assertIsNone(info)
    
    def test_find_openapi_files(self):
        """Test finding OpenAPI files in a directory."""
        openapi_files = find_openapi_files(self.temp_dir)
        
        self.assertEqual(len(openapi_files), 2)
        
        # Check that both files were found
        file_names = [os.path.basename(f["file"]) for f in openapi_files]
        self.assertIn("swagger.json", file_names)
        self.assertIn("openapi.yaml", file_names)
    
    def test_generate_openapi_spec(self):
        """Test generating an OpenAPI specification from endpoints."""
        endpoints = [
            {
                "path": "/api/users",
                "method": "GET",
                "file": "users.py",
                "line": 10
            },
            {
                "path": "/api/users",
                "method": "POST",
                "file": "users.py",
                "line": 20
            },
            {
                "path": "/api/users/{id}",
                "method": "GET",
                "file": "users.py",
                "line": 30
            }
        ]
        
        spec = generate_openapi_spec(endpoints, "test-repo")
        
        # Check basic structure
        self.assertEqual(spec["openapi"], "3.0.0")
        self.assertEqual(spec["info"]["title"], "API Documentation for test-repo")
        
        # Check paths
        self.assertIn("/api/users", spec["paths"])
        self.assertIn("/api/users/{id}", spec["paths"])
        
        # Check methods
        self.assertIn("get", spec["paths"]["/api/users"])
        self.assertIn("post", spec["paths"]["/api/users"])
        self.assertIn("get", spec["paths"]["/api/users/{id}"])
    
    def test_save_generated_openapi(self):
        """Test saving a generated OpenAPI specification."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {}
        }
        
        output_dir = os.path.join(self.temp_dir, "output")
        output_path = save_generated_openapi(spec, output_dir, "test-repo", "json")
        
        # Check that the file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Check that the content is correct
        with open(output_path, 'r') as f:
            saved_spec = json.load(f)
        
        self.assertEqual(saved_spec["openapi"], "3.0.0")
        self.assertEqual(saved_spec["info"]["title"], "Test API")


if __name__ == "__main__":
    unittest.main()