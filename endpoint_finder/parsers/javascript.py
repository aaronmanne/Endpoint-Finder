"""
JavaScript parser for detecting API endpoints in Express.js applications.
"""

import re
import logging
from typing import List, Dict, Any

from endpoint_finder.parsers.base import BaseParser

# Configure logging
logger = logging.getLogger(__name__)


class JavaScriptParser(BaseParser):
    """
    Parser for JavaScript files to detect API endpoints in Express.js applications.
    """
    
    def parse(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a JavaScript file for API endpoints.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        
        # Try to use esprima if available for more accurate parsing
        try:
            import esprima
            ast_endpoints = self._parse_with_esprima(content, file_path)
            endpoints.extend(ast_endpoints)
        except ImportError:
            logger.warning("esprima not available, falling back to regex parsing")
            regex_endpoints = self._parse_with_regex(content, file_path)
            endpoints.extend(regex_endpoints)
        except Exception as e:
            logger.warning(f"Error parsing {file_path} with esprima: {e}, falling back to regex parsing")
            regex_endpoints = self._parse_with_regex(content, file_path)
            endpoints.extend(regex_endpoints)
        
        return endpoints
    
    def _parse_with_esprima(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a JavaScript file for API endpoints using esprima.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        import esprima
        
        endpoints = []
        
        # Parse the JavaScript code
        try:
            ast = esprima.parseScript(content, {'loc': True, 'comment': True})
        except:
            # Try parsing as module if script parsing fails
            try:
                ast = esprima.parseModule(content, {'loc': True, 'comment': True})
            except Exception as e:
                logger.warning(f"Error parsing {file_path} with esprima: {e}")
                return []
        
        # Find Express.js route definitions
        self._find_express_routes(ast.body, endpoints, file_path)
        
        return endpoints
    
    def _find_express_routes(self, nodes, endpoints, file_path, router_var=None):
        """
        Recursively find Express.js route definitions in the AST.
        
        Args:
            nodes: List of AST nodes to search.
            endpoints: List to append found endpoints to.
            file_path: Path to the file being parsed.
            router_var: Name of the router variable, if known.
        """
        import esprima
        
        for node in nodes:
            # Look for app.METHOD() or router.METHOD() calls
            if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
                call_expr = node.expression
                
                # Check if it's a method call on an object
                if call_expr.callee.type == 'MemberExpression':
                    obj = call_expr.callee.object
                    method = call_expr.callee.property.name.lower() if hasattr(call_expr.callee.property, 'name') else None
                    
                    # Check if it's a route method (get, post, put, delete, etc.)
                    if method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'all', 'use']:
                        # Check if it's called on app, router, or a known router variable
                        obj_name = obj.name if hasattr(obj, 'name') else None
                        
                        if obj_name in ['app', 'router'] or obj_name == router_var:
                            # Extract the route path from the first argument
                            if call_expr.arguments and len(call_expr.arguments) > 0:
                                path_arg = call_expr.arguments[0]
                                
                                # Extract the path string
                                path = None
                                if path_arg.type == 'Literal' and isinstance(path_arg.value, str):
                                    path = path_arg.value
                                
                                if path is not None:
                                    # Add the endpoint
                                    endpoints.append({
                                        "path": path,
                                        "method": method.upper(),
                                        "framework": "Express.js",
                                        "file": file_path,
                                        "line": node.loc.start.line,
                                        "function": "anonymous",  # Could try to extract handler function name
                                        "description": self._extract_comment(node) or ""
                                    })
            
            # Look for router definitions
            elif node.type == 'VariableDeclaration':
                for decl in node.declarations:
                    if decl.init and decl.init.type == 'CallExpression':
                        if (decl.init.callee.type == 'MemberExpression' and 
                            hasattr(decl.init.callee.object, 'name') and 
                            decl.init.callee.object.name == 'express' and 
                            hasattr(decl.init.callee.property, 'name') and 
                            decl.init.callee.property.name == 'Router'):
                            
                            # Found a router definition, remember the variable name
                            if hasattr(decl.id, 'name'):
                                router_var = decl.id.name
            
            # Recursively search in block statements
            if hasattr(node, 'body'):
                if isinstance(node.body, list):
                    self._find_express_routes(node.body, endpoints, file_path, router_var)
                elif hasattr(node.body, 'body') and isinstance(node.body.body, list):
                    self._find_express_routes(node.body.body, endpoints, file_path, router_var)
    
    def _extract_comment(self, node):
        """
        Extract a comment from a node, if available.
        
        Args:
            node: AST node to extract a comment from.
            
        Returns:
            str: Comment text, or empty string if no comment is available.
        """
        # This is a simplified implementation
        # A more robust implementation would need to track comments in the AST
        return ""
    
    def _parse_with_regex(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a JavaScript file for API endpoints using regular expressions.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints = []
        
        # Split content into lines for line number tracking
        lines = content.split('\n')
        
        # Express.js route patterns
        # app.METHOD(path, ...handlers)
        # router.METHOD(path, ...handlers)
        express_route_pattern = r'(?:app|router|[A-Za-z_$][A-Za-z0-9_$]*)\.(get|post|put|delete|patch|options|head|all|use)\s*\(\s*[\'"]([^\'"]+)[\'"]'
        
        # Find Express.js routes
        for i, line in enumerate(lines):
            for match in re.finditer(express_route_pattern, line):
                method = match.group(1).upper()
                path = match.group(2)
                
                endpoints.append({
                    "path": path,
                    "method": method,
                    "framework": "Express.js",
                    "file": file_path,
                    "line": i + 1,
                    "function": "anonymous",
                    "description": ""
                })
        
        return endpoints