"""
OpenAPI/Swagger documentation functionality for Endpoint Finder.

This module provides functionality to:
1. Find and save existing OpenAPI/Swagger documentation in repositories
2. Generate OpenAPI/Swagger documentation from detected endpoints
"""

import os
import re
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Common OpenAPI/Swagger file patterns
OPENAPI_FILE_PATTERNS = [
    r'swagger\.(json|yaml|yml)$',
    r'openapi\.(json|yaml|yml)$',
    r'api-docs\.(json|yaml|yml)$',
    r'api-specification\.(json|yaml|yml)$',
    r'swagger-config\.(json|yaml|yml)$',
    r'openapi-config\.(json|yaml|yml)$',
]

def find_openapi_files(repo_path: str) -> List[Dict[str, Any]]:
    """
    Find OpenAPI/Swagger documentation files in a repository.
    
    Args:
        repo_path (str): Path to the repository.
        
    Returns:
        List[Dict[str, Any]]: List of found OpenAPI files with metadata.
    """
    logger.info(f"Searching for OpenAPI/Swagger documentation in {repo_path}")
    
    openapi_files = []
    
    # Walk through the repository
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)
            
            # Skip files in common source library directories
            if any(part in file_path.lower() for part in ['node_modules', 'vendor', 'third_party']):
                continue
            
            # Check if the file matches any OpenAPI pattern
            if any(re.search(pattern, file, re.IGNORECASE) for pattern in OPENAPI_FILE_PATTERNS):
                try:
                    # Try to parse the file to verify it's a valid OpenAPI/Swagger document
                    spec_format, spec_version, spec_info = validate_openapi_file(file_path)
                    if spec_format:
                        openapi_files.append({
                            "file": rel_path,
                            "format": spec_format,
                            "version": spec_version,
                            "info": spec_info,
                            "path": file_path
                        })
                        logger.info(f"Found OpenAPI/Swagger file: {rel_path} (version: {spec_version})")
                except Exception as e:
                    logger.debug(f"File {rel_path} matches OpenAPI pattern but is not a valid specification: {e}")
    
    return openapi_files

def validate_openapi_file(file_path: str) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate if a file is a valid OpenAPI/Swagger specification.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]: 
            - Format (json/yaml)
            - OpenAPI/Swagger version
            - Info object from the specification
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            file_format = "json"
        except json.JSONDecodeError:
            # If not JSON, try YAML
            try:
                data = yaml.safe_load(content)
                file_format = "yaml"
            except yaml.YAMLError:
                return None, None, None
        
        # Check if it's a valid OpenAPI/Swagger document
        if "swagger" in data:
            # Swagger 2.0
            version = data.get("swagger")
            info = data.get("info", {})
            return file_format, f"Swagger {version}", info
        elif "openapi" in data:
            # OpenAPI 3.x
            version = data.get("openapi")
            info = data.get("info", {})
            return file_format, f"OpenAPI {version}", info
        
        return None, None, None
    
    except Exception as e:
        logger.debug(f"Error validating OpenAPI file {file_path}: {e}")
        return None, None, None

def save_openapi_file(openapi_file: Dict[str, Any], output_dir: str) -> str:
    """
    Save an OpenAPI/Swagger file to the output directory.
    
    Args:
        openapi_file (Dict[str, Any]): OpenAPI file metadata.
        output_dir (str): Directory to save the file to.
        
    Returns:
        str: Path to the saved file.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    filename = os.path.basename(openapi_file["file"])
    output_path = os.path.join(output_dir, filename)
    
    # Copy the file
    with open(openapi_file["path"], 'r', encoding='utf-8', errors='ignore') as src:
        content = src.read()
        
        with open(output_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
    
    logger.info(f"Saved OpenAPI/Swagger file to {output_path}")
    return output_path

def extract_path_parameters(path: str):
    # Find all {param} in the path
    return re.findall(r'\{([^}]+)\}', path)

def generate_openapi_spec(endpoints: List[Dict[str, Any]], repo_name: str, output_format: str = "json") -> Dict[str, Any]:
    """
    Generate an OpenAPI specification from detected endpoints.
    
    Args:
        endpoints (List[Dict[str, Any]]): List of detected endpoints.
        repo_name (str): Name of the repository.
        output_format (str): Output format (json or yaml).
        
    Returns:
        Dict[str, Any]: Generated OpenAPI specification.
    """
    logger.info(f"Generating OpenAPI specification for {repo_name} with {len(endpoints)} endpoints")
    
    # Create basic OpenAPI structure
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": f"API Documentation for {repo_name}",
            "description": f"Automatically generated API documentation for {repo_name}",
            "version": "1.0.0"
        },
        "paths": {}
    }
    
    # Group endpoints by path
    path_groups = {}
    for endpoint in endpoints:
        path = endpoint.get("path", "/")
        if path not in path_groups:
            path_groups[path] = []
        path_groups[path].append(endpoint)
    
    # Add paths and operations to the specification
    for path, path_endpoints in path_groups.items():
        # Clean up path format - remove any trailing quotes, produces annotations, or other metadata
        # First, check if the path contains a produces annotation or other metadata
        if '"' in path:
            # Extract the actual path by taking everything before the first quote that's not part of a path parameter
            parts = path.split('"')
            if len(parts) > 1:
                clean_path = parts[0]
            else:
                clean_path = path
        else:
            clean_path = path
        
        # Remove any trailing non-path characters
        clean_path = re.sub(r'[,"\s]+$', '', clean_path).strip()
        
        # Log the path cleaning for debugging
        logger.debug(f"Original path: {path}")
        logger.debug(f"Cleaned path: {clean_path}")
        
        # Skip paths that couldn't be properly cleaned
        if not clean_path or clean_path.endswith('"'):
            logger.warning(f"Skipping path that couldn't be properly cleaned: {path}")
            continue
            
        # Initialize the path in the spec if it doesn't exist
        if clean_path not in spec["paths"]:
            spec["paths"][clean_path] = {}
        
        # Extract path parameters from the URL pattern
        path_params = extract_path_parameters(clean_path)
        
        for endpoint in path_endpoints:
            method = endpoint.get("method", "get").lower()
            if method not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue
                
            operation = {
                "summary": f"{method.upper()} {clean_path}",
                "description": f"Source: {endpoint.get('file', 'Unknown')}",
                "responses": {
                    "200": {
                        "description": "Successful operation"
                    }
                }
            }
            
            # Initialize parameters list
            operation["parameters"] = []
            
            # Add path parameters from URL pattern
            for param in path_params:
                operation["parameters"].append({
                    "name": param,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                })
                
            # Add path parameters from annotations
            for param in endpoint.get("path_params", []):
                # Check if this parameter is already included from the URL pattern
                if param not in path_params:
                    operation["parameters"].append({
                        "name": param,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    })
            
            # Add additional parameters if present in endpoint
            if "parameters" in endpoint:
                operation["parameters"].extend(endpoint["parameters"])

            # Add query, header, and cookie parameters
            for param_type, param_in in [("query_params", "query"), ("header_params", "header"),
                                         ("cookie_params", "cookie")]:
                for param in endpoint.get(param_type, []):
                    operation["parameters"].append({
                        "name": param,
                        "in": param_in,
                        "required": False,
                        "schema": {"type": "string"}
                    })

            # Add request body for appropriate methods or if explicitly marked
            if (method in ["post", "put", "patch"] and "request_body" not in operation) or endpoint.get("has_request_body", False):
                operation["requestBody"] = {
                    "description": "Request body",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                }
            # Use the cleaned path, not the original path
            spec["paths"][clean_path][method] = operation
    return spec

def save_generated_openapi(spec: Dict[str, Any], output_dir: str, repo_name: str, output_format: str = "json") -> str:
    """
    Save a generated OpenAPI specification to a file.
    
    Args:
        spec (Dict[str, Any]): OpenAPI specification.
        output_dir (str): Directory to save the file to.
        repo_name (str): Name of the repository.
        output_format (str): Output format (json or yaml).
        
    Returns:
        str: Path to the saved file.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    filename = f"openapi-{repo_name}.{output_format}"
    output_path = os.path.join(output_dir, filename)
    
    # Write the specification to file
    with open(output_path, 'w', encoding='utf-8') as f:
        if output_format == "json":
            json.dump(spec, f, indent=2)
        else:
            yaml.dump(spec, f, sort_keys=False)
    
    logger.info(f"Saved generated OpenAPI specification to {output_path}")
    return output_path