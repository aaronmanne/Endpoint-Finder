"""
Java parser for detecting API endpoints in Spring Boot applications.
"""

import re
import logging
from typing import List, Dict, Any
import javalang
from javalang import tree

from endpoint_finder.parsers.base import BaseParser

# Configure logging
logger = logging.getLogger(__name__)


class JavaParser(BaseParser):
    """
    Parser for Java files to detect API endpoints in Spring Boot applications.
    """
    
    def parse(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Java file for API endpoints.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        
        # Try to use javalang if available for more accurate parsing
        try:
            ast_endpoints = self._parse_with_javalang(content, file_path)
            endpoints.extend(ast_endpoints)
        except ImportError:
            logger.warning("javalang not available, falling back to regex parsing")
            regex_endpoints = self._parse_with_regex(content, file_path)
            endpoints.extend(regex_endpoints)
        except Exception as e:
            logger.warning(f"Error parsing {file_path} with javalang: {e}, falling back to regex parsing")
            regex_endpoints = self._parse_with_regex(content, file_path)
            endpoints.extend(regex_endpoints)
        
        return endpoints
    
    def _parse_with_javalang(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Java file for API endpoints using javalang.
        """
        endpoints = []
        
        try:
            # Parse the Java code
            tree = javalang.parse.parse(content)
            
            # Find Spring Boot controller classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                # Check if class has @RestController or @Controller annotation
                is_controller = False
                class_mapping = "/"
                
                # Check class annotations including meta-annotations
                for annotation in node.annotations:
                    if annotation.name in ['RestController', 'Controller']:
                        is_controller = True
                    elif annotation.name == 'RequestMapping':
                        class_mapping = self._extract_mapping_path(annotation) or "/"
            
                if is_controller:
                    # Process methods in the controller
                    for method_node in node.methods:
                        method_endpoints = self._process_controller_method(method_node, class_mapping, file_path)
                        endpoints.extend(method_endpoints)
        
            return endpoints
    
        except Exception as e:
            logger.warning(f"Error parsing {file_path} with javalang: {e}")
            # Only fall back to regex if we couldn't parse the file at all
            if not endpoints:
                logger.info("No endpoints found with AST parsing, trying regex")
                return self._parse_with_regex(content, file_path)
            return endpoints
    
    def _process_controller_method(self, method_node, class_mapping: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a method in a controller class to extract endpoints.
        
        Args:
            method_node: Method node from javalang AST.
            class_mapping: Base path from class-level RequestMapping, if any.
            file_path: Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the method.
        """

        endpoints = []
        for annotation in method_node.annotations:
            mapping_info = self._extract_mapping_info(annotation)
            if mapping_info:
                path, methods = mapping_info
                if class_mapping:
                    if path.startswith('/'):
                        path = class_mapping + path
                    else:
                        path = class_mapping + '/' + path
                if not path.startswith('/'):
                    path = '/' + path
                for method in methods:
                    endpoint = {
                        "path": path,
                        "method": method,
                        "framework": "Spring Boot",
                        "file": file_path,
                        "line": method_node.position.line if hasattr(method_node, 'position') else 0,
                        "function": method_node.name,
                        "description": self._extract_javadoc(method_node) or "",
                        "query_params": [],
                        "header_params": [],
                        "cookie_params": [],
                        "path_params": [],
                        "has_request_body": False
                    }
                    # --- Extract parameter annotations ---
                    for param in getattr(method_node, "parameters", []):
                        for param_ann in getattr(param, "annotations", []):
                            # Extract parameter name from annotation value if available
                            param_name = param.name  # Default to variable name
                            
                            # Check if annotation has elements (like value="something")
                            if hasattr(param_ann, 'element') and param_ann.element:
                                for pair in param_ann.element:
                                    # Look for 'value' or unnamed element
                                    if pair.name in ['value', None]:
                                        extracted_name = self._extract_string_literal(pair.value)
                                        if extracted_name and extracted_name != "/":
                                            param_name = extracted_name
                                            break
                            
                            if param_ann.name == "RequestParam":
                                endpoint["query_params"].append(param_name)
                            elif param_ann.name == "RequestHeader":
                                # Special case for Authorization header
                                if param_name.lower() == "authorization" or param.name.lower() == "authorization":
                                    param_name = "Authorization"
                                endpoint["header_params"].append(param_name)
                            elif param_ann.name == "CookieValue":
                                endpoint["cookie_params"].append(param_name)
                            elif param_ann.name == "PathVariable":
                                endpoint["path_params"].append(param_name)
                            elif param_ann.name == "RequestBody":
                                endpoint["has_request_body"] = True
                    endpoints.append(endpoint)
        return endpoints
    
    def _extract_mapping_info(self, annotation) -> tuple:
        """
        Extract path and HTTP methods from a mapping annotation.
        """
        # Check if it's a mapping annotation
        if annotation.name in ['RequestMapping', 'GetMapping', 'PostMapping', 'PutMapping', 
                              'DeleteMapping', 'PatchMapping']:
            
            # Default values
            path = "/"
            methods = []
            
            # Set methods based on annotation type
            method_map = {
                'GetMapping': ['GET'],
                'PostMapping': ['POST'],
                'PutMapping': ['PUT'],
                'DeleteMapping': ['DELETE'],
                'PatchMapping': ['PATCH'],
                'RequestMapping': ['GET']  # Default for RequestMapping
            }
            
            methods = method_map.get(annotation.name, ['GET'])
            
            # Extract path and methods from annotation elements
            if hasattr(annotation, 'element') and annotation.element:
                for pair in annotation.element:
                    # Handle path from 'value' or 'path' attributes
                    if pair.name in ['value', 'path']:
                        if isinstance(pair.value, list):
                            paths = []
                            for path_node in pair.value:
                                path_value = self._extract_string_literal(path_node)
                                if path_value:
                                    paths.append(path_value)
                            if paths:
                                path = paths[0]  # Use first path if multiple defined
                        else:
                            path_value = self._extract_string_literal(pair.value)
                            if path_value:
                                path = path_value

                    # Handle HTTP methods for RequestMapping
                    elif pair.name == 'method' and annotation.name == 'RequestMapping':
                        methods = []
                        if isinstance(pair.value, list):
                            for method_ref in pair.value:
                                method = self._extract_method_from_reference(method_ref)
                                if method:
                                    methods.append(method)
                        else:
                            method = self._extract_method_from_reference(pair.value)
                            if method:
                                methods.append(method)

                        if not methods:  # Fallback to GET if no valid methods found
                            methods = ['GET']

                    return path, methods

            return None
    
    def _extract_mapping_path(self, annotation) -> str:
        """
        Extract path from a RequestMapping annotation.
        
        Args:
            annotation: Annotation node from javalang AST.
            
        Returns:
            str: Path from the annotation, or "/" if not found.
        """
        path = "/"

        if hasattr(annotation, 'element') and annotation.element:
            for pair in annotation.element:
                if pair.name == 'value' or pair.name == 'path':
                    if isinstance(pair.value, list):
                        if pair.value:  # Use first path if multiple are defined
                            path = self._extract_string_literal(pair.value[0])
                    else:
                        path = self._extract_string_literal(pair.value)
        
        return path
    
    def _extract_string_literal(self, node) -> str:
        """
        Extract a string literal from a node.
        
        Args:
            node: Node from javalang AST.
            
        Returns:
            str: String literal value, or "/" if not a string literal.
        """
        if hasattr(node, 'value') and isinstance(node.value, str):
            return node.value
        return "/"
    
    def _extract_method_from_reference(self, node) -> str:
        """
        Extract HTTP method from a RequestMethod reference.
        """
        if hasattr(node, 'member'):
            method = node.member
            # Extended list of valid HTTP methods
            valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'TRACE']
            if method in valid_methods:
                return method
            # Handle cases where the method might include the RequestMethod prefix
            elif method.startswith('REQUEST_METHOD_'):
                clean_method = method.replace('REQUEST_METHOD_', '')
                if clean_method in valid_methods:
                    return clean_method
        return None
    
    def _extract_javadoc(self, node) -> str:
        """
        Extract Javadoc comment from a node.
        
        Args:
            node: Node from javalang AST.
            
        Returns:
            str: Javadoc comment, or empty string if not found.
        """
        # This is a simplified implementation
        # A more robust implementation would need to track comments in the AST
        return ""
    
    def _parse_with_regex(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a Java file for API endpoints using regular expressions.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        
        # Split content into lines for line number tracking
        lines = content.split('\n')
        
        # Check if this is a controller class
        is_controller = False
        class_mapping = ""
        
        # Look for controller annotations
        controller_pattern = r'@(?:RestController|Controller)'
        class_mapping_pattern = r'@RequestMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*\)'
        
        # Method mapping patterns
        method_mapping_patterns = {
            r'@GetMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*\)': 'GET',
            r'@PostMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*\)': 'POST',
            r'@PutMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*\)': 'PUT',
            r'@DeleteMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*\)': 'DELETE',
            r'@PatchMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*\)': 'PATCH',
            r'@RequestMapping\s*\(\s*(?:value\s*=\s*|\s*)["\'](.*?)["\']\s*(?:,\s*method\s*=\s*(?:RequestMethod\.)?([A-Z]+))?': None
        }
        
        # First pass: check if this is a controller and get class-level mapping
        for line in lines:
            if re.search(controller_pattern, line):
                is_controller = True
            
            class_mapping_match = re.search(class_mapping_pattern, line)
            if class_mapping_match:
                class_mapping = class_mapping_match.group(1)
                if not class_mapping.startswith('/'):
                    class_mapping = '/' + class_mapping
        
        # If not a controller, no need to continue
        if not is_controller:
            return endpoints
        
        # Second pass: find method mappings
        for i, line in enumerate(lines):
            for pattern, default_method in method_mapping_patterns.items():
                for match in re.finditer(pattern, line):
                    path = match.group(1)
                    
                    # For RequestMapping, try to get the method
                    if default_method is None:
                        method = match.group(2) if len(match.groups()) > 1 and match.group(2) else 'GET'
                    else:
                        method = default_method
                    
                    # Combine class-level and method-level paths
                    if class_mapping:
                        if path.startswith('/'):
                            path = class_mapping + path
                        else:
                            path = class_mapping + '/' + path
                    
                    # Ensure path starts with /
                    if not path.startswith('/'):
                        path = '/' + path
                    
                    # Create endpoint with parameter lists
                    endpoint = {
                        "path": path,
                        "method": method,
                        "framework": "Spring Boot",
                        "file": file_path,
                        "line": i + 1,
                        "function": "unknown",  # Can't reliably get method name with regex
                        "description": "",
                        "query_params": [],
                        "header_params": [],
                        "cookie_params": [],
                        "path_params": [],
                        "has_request_body": False
                    }
                    
                    # Look for method parameters in the next few lines
                    param_search_range = 10  # Look at up to 10 lines after the mapping
                    for j in range(i + 1, min(i + param_search_range, len(lines))):
                        param_line = lines[j]
                        
                        # Check for path parameters - find all matches in the line
                        path_param_matches = re.finditer(r'@PathVariable\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'])?\s*\)?\s*(?:\w+\s+)?(\w+)', param_line)
                        for path_param_match in path_param_matches:
                            # Use annotation value if available, otherwise use variable name
                            param_name = path_param_match.group(1) if path_param_match.group(1) else path_param_match.group(2)
                            endpoint["path_params"].append(param_name)
                        
                        # Check for query parameters - find all matches in the line
                        query_param_matches = re.finditer(r'@RequestParam\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'])?\s*\)?\s*(?:\w+\s+)?(\w+)', param_line)
                        for query_param_match in query_param_matches:
                            # Use annotation value if available, otherwise use variable name
                            param_name = query_param_match.group(1) if query_param_match.group(1) else query_param_match.group(2)
                            endpoint["query_params"].append(param_name)
                        
                        # Check for header parameters - find all matches in the line
                        header_param_matches = re.finditer(r'@RequestHeader\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'])?\s*\)?\s*(?:\w+\s+)?(\w+)', param_line)
                        for header_param_match in header_param_matches:
                            # Use annotation value if available, otherwise use variable name
                            param_name = header_param_match.group(1) if header_param_match.group(1) else header_param_match.group(2)
                            # Special case for Authorization header
                            if param_name and param_name.lower() == "authorization":
                                param_name = "Authorization"
                            endpoint["header_params"].append(param_name)
                        
                        # Check for cookie parameters - find all matches in the line
                        cookie_param_matches = re.finditer(r'@CookieValue\s*(?:\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\'])?\s*\)?\s*(?:\w+\s+)?(\w+)', param_line)
                        for cookie_param_match in cookie_param_matches:
                            # Use annotation value if available, otherwise use variable name
                            param_name = cookie_param_match.group(1) if cookie_param_match.group(1) else cookie_param_match.group(2)
                            endpoint["cookie_params"].append(param_name)
                        
                        # Check for request body
                        request_body_match = re.search(r'@RequestBody', param_line)
                        if request_body_match:
                            endpoint["has_request_body"] = True
                        
                        # Stop searching if we hit a closing brace or another method
                        if re.search(r'^\s*\}\s*$', param_line) or re.search(r'@\w+Mapping', param_line):
                            break
                    
                    endpoints.append(endpoint)
        
        return endpoints

    def _combine_paths(self, base_path: str, method_path: str) -> str:
        """
        Properly combine base path and method path.
        """
        if not base_path:
            base_path = "/"
        if not method_path:
            method_path = "/"
            
        # Ensure paths start with /
        if not base_path.startswith('/'):
            base_path = '/' + base_path
        if not method_path.startswith('/'):
            method_path = '/' + method_path
            
        # Combine paths
        if base_path.endswith('/'):
            base_path = base_path[:-1]
        if method_path == '/':
            return base_path
            
        return base_path + method_path