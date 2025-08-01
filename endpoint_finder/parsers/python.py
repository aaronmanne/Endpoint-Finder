"""
Python parser for detecting API endpoints in Flask, Django, and FastAPI applications.
"""

import re
import ast
import logging
from typing import List, Dict, Any, Optional, Tuple

from endpoint_finder.parsers.base import BaseParser

# Configure logging
logger = logging.getLogger(__name__)


class PythonParser(BaseParser):
    """
    Parser for Python files to detect API endpoints in Flask, Django, and FastAPI applications.
    """
    
    def parse(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Python file for API endpoints.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        
        # Try AST parsing first for more accurate results
        try:
            ast_endpoints = self._parse_with_ast(content, file_path)
            endpoints.extend(ast_endpoints)
        except SyntaxError:
            logger.warning(f"Syntax error in {file_path}, falling back to regex parsing")
        
        # If no endpoints found with AST, try regex as a fallback
        if not endpoints:
            regex_endpoints = self._parse_with_regex(content, file_path)
            endpoints.extend(regex_endpoints)
        
        return endpoints
    
    def _parse_with_ast(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Python file for API endpoints using AST.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        tree = ast.parse(content)
        
        # Look for Flask endpoints
        flask_endpoints = self._find_flask_endpoints(tree, content, file_path)
        endpoints.extend(flask_endpoints)
        
        # Look for Django endpoints
        django_endpoints = self._find_django_endpoints(tree, content, file_path)
        endpoints.extend(django_endpoints)
        
        # Look for FastAPI endpoints
        fastapi_endpoints = self._find_fastapi_endpoints(tree, content, file_path)
        endpoints.extend(fastapi_endpoints)
        
        return endpoints
    
    def _find_flask_endpoints(self, tree: ast.AST, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Find Flask endpoints in an AST.
        
        Args:
            tree (ast.AST): AST of the Python file.
            content (str): Content of the file.
            file_path (str): Path to the file.
            
        Returns:
            List[Dict[str, Any]]: List of Flask endpoints found in the file.
        """
        endpoints = []
        
        # Look for app.route decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    route_info = self._extract_flask_route(decorator, content)
                    if route_info:
                        path, methods = route_info
                        for method in methods:
                            endpoints.append({
                                "path": path,
                                "method": method,
                                "framework": "Flask",
                                "file": file_path,
                                "line": node.lineno,
                                "function": node.name,
                                "description": ast.get_docstring(node) or ""
                            })
        
        return endpoints
    
    def _extract_flask_route(self, decorator: ast.expr, content: str) -> Optional[Tuple[str, List[str]]]:
        """
        Extract route information from a Flask route decorator.
        
        Args:
            decorator (ast.expr): Decorator AST node.
            content (str): Content of the file.
            
        Returns:
            Optional[Tuple[str, List[str]]]: Tuple of (path, methods) if the decorator is a Flask route, None otherwise.
        """
        # Check for app.route() or blueprint.route()
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'route':
                # Extract path from first argument
                if decorator.args:
                    path = self._extract_string_value(decorator.args[0])
                    if path:
                        # Extract methods from keyword arguments
                        methods = ['GET']  # Default method is GET
                        for keyword in decorator.keywords:
                            if keyword.arg == 'methods':
                                if isinstance(keyword.value, ast.List):
                                    methods = [self._extract_string_value(elt) for elt in keyword.value.elts]
                                    methods = [m for m in methods if m]  # Filter out None values
                        return path, methods
        
        # Check for app.get(), app.post(), etc.
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                method = decorator.func.attr.upper()
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']:
                    if decorator.args:
                        path = self._extract_string_value(decorator.args[0])
                        if path:
                            return path, [method]
        
        return None
    
    def _find_django_endpoints(self, tree: ast.AST, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Find Django endpoints in an AST.
        
        Args:
            tree (ast.AST): AST of the Python file.
            content (str): Content of the file.
            file_path (str): Path to the file.
            
        Returns:
            List[Dict[str, Any]]: List of Django endpoints found in the file.
        """
        endpoints = []
        
        # Look for path() or url() function calls in urlpatterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'urlpatterns':
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                django_endpoint = self._extract_django_path(elt, content, file_path)
                                if django_endpoint:
                                    endpoints.append(django_endpoint)
        
        return endpoints
    
    def _extract_django_path(self, node: ast.expr, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract endpoint information from a Django path() or url() function call.
        
        Args:
            node (ast.expr): AST node representing the function call.
            content (str): Content of the file.
            file_path (str): Path to the file.
            
        Returns:
            Optional[Dict[str, Any]]: Endpoint information if the node is a Django path, None otherwise.
        """
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            
            if func_name in ['path', 'url', 're_path']:
                if len(node.args) >= 2:
                    path = self._extract_string_value(node.args[0])
                    
                    # Try to extract view name
                    view_name = None
                    if isinstance(node.args[1], ast.Name):
                        view_name = node.args[1].id
                    elif isinstance(node.args[1], ast.Attribute):
                        view_name = node.args[1].attr
                    
                    if path:
                        return {
                            "path": path,
                            "method": "",  # Django URLs don't specify HTTP method directly
                            "framework": "Django",
                            "file": file_path,
                            "line": node.lineno,
                            "function": view_name or "unknown",
                            "description": ""
                        }
        
        return None
    
    def _find_fastapi_endpoints(self, tree: ast.AST, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Find FastAPI endpoints in an AST.
        
        Args:
            tree (ast.AST): AST of the Python file.
            content (str): Content of the file.
            file_path (str): Path to the file.
            
        Returns:
            List[Dict[str, Any]]: List of FastAPI endpoints found in the file.
        """
        endpoints = []
        
        # Look for @app.get, @app.post, etc. decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    fastapi_endpoint = self._extract_fastapi_route(decorator, node, content, file_path)
                    if fastapi_endpoint:
                        endpoints.append(fastapi_endpoint)
        
        return endpoints
    
    def _extract_fastapi_route(self, decorator: ast.expr, func_def: ast.FunctionDef, content: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract endpoint information from a FastAPI route decorator.
        
        Args:
            decorator (ast.expr): Decorator AST node.
            func_def (ast.FunctionDef): Function definition AST node.
            content (str): Content of the file.
            file_path (str): Path to the file.
            
        Returns:
            Optional[Dict[str, Any]]: Endpoint information if the decorator is a FastAPI route, None otherwise.
        """
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                method = decorator.func.attr.upper()
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']:
                    if decorator.args:
                        path = self._extract_string_value(decorator.args[0])
                        if path:
                            return {
                                "path": path,
                                "method": method,
                                "framework": "FastAPI",
                                "file": file_path,
                                "line": func_def.lineno,
                                "function": func_def.name,
                                "description": ast.get_docstring(func_def) or ""
                            }
        
        return None
    
    def _extract_string_value(self, node: ast.expr) -> Optional[str]:
        """
        Extract a string value from an AST node.
        
        Args:
            node (ast.expr): AST node to extract a string value from.
            
        Returns:
            Optional[str]: String value if the node is a string literal, None otherwise.
        """
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None
    
    def _parse_with_regex(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Python file for API endpoints using regular expressions.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        
        # Split content into lines for line number tracking
        lines = content.split('\n')
        
        # Flask patterns
        flask_route_pattern = r'@(?:\w+)\.route\([\'"]([^\'"]+)[\'"](,\s*methods=\[([^\]]+)\])?'
        flask_method_pattern = r'@(?:\w+)\.(get|post|put|delete|patch|options|head)\([\'"]([^\'"]+)[\'"]\)'
        
        # Django patterns
        django_path_pattern = r'(?:path|url|re_path)\([\'"]([^\'"]+)[\'"]\s*,\s*(\w+(?:\.\w+)*)'
        
        # FastAPI patterns
        fastapi_pattern = r'@(?:\w+)\.(get|post|put|delete|patch|options|head)\([\'"]([^\'"]+)[\'"]\)'
        
        # Find Flask routes
        for i, line in enumerate(lines):
            # Check for Flask app.route()
            for match in re.finditer(flask_route_pattern, line):
                path = match.group(1)
                methods_str = match.group(3) if match.group(3) else "'GET'"
                methods = [m.strip().strip("'\"") for m in methods_str.split(',')]
                
                for method in methods:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "framework": "Flask",
                        "file": file_path,
                        "line": i + 1,
                        "function": "unknown",  # Can't reliably get function name with regex
                        "description": ""
                    })
            
            # Check for Flask app.get(), app.post(), etc.
            for match in re.finditer(flask_method_pattern, line):
                method = match.group(1).upper()
                path = match.group(2)
                
                endpoints.append({
                    "path": path,
                    "method": method,
                    "framework": "Flask",
                    "file": file_path,
                    "line": i + 1,
                    "function": "unknown",
                    "description": ""
                })
            
            # Check for Django path() or url()
            for match in re.finditer(django_path_pattern, line):
                path = match.group(1)
                view = match.group(2)
                
                endpoints.append({
                    "path": path,
                    "method": "",
                    "framework": "Django",
                    "file": file_path,
                    "line": i + 1,
                    "function": view,
                    "description": ""
                })
            
            # Check for FastAPI app.get(), app.post(), etc.
            for match in re.finditer(fastapi_pattern, line):
                method = match.group(1).upper()
                path = match.group(2)
                
                endpoints.append({
                    "path": path,
                    "method": method,
                    "framework": "FastAPI",
                    "file": file_path,
                    "line": i + 1,
                    "function": "unknown",
                    "description": ""
                })
        
        return endpoints