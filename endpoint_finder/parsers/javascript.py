"""
JavaScript parser for detecting API endpoints in Express.js applications.
"""

import logging
import re
import traceback
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
        # Prefer regex-based parsing for robustness and simple mount composition
        try:
            regex_endpoints = self._parse_with_regex(content, file_path)
            endpoints.extend(regex_endpoints)
        except Exception as e:
            logger.error(f"Regex parsing failed for {file_path}: {e}")
        return endpoints
    
    def _parse_with_esprima(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a JavaScript/TypeScript file for API endpoints using esprima.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        import esprima
        
        endpoints = []
        file_ext = file_path.split('.')[-1].lower()
        
        # For TypeScript files, try to preprocess the content
        if file_ext in ['ts', 'tsx']:
            # Remove TypeScript type annotations that might cause parsing issues
            # This is a simple approach - more complex TypeScript features might still cause issues
            content = self._preprocess_typescript(content)
        
        # Parse the JavaScript/TypeScript code
        try:
            ast = esprima.parseScript(content, {'loc': True, 'comment': True})
        except:
            # Try parsing as module if script parsing fails
            try:
                ast = esprima.parseModule(content, {'loc': True, 'comment': True})
            except Exception as e:
                if file_ext in ['ts', 'tsx']:
                    tb = traceback.extract_tb(e.__traceback__)
                    last_frame = tb[-1]
                    logger.debug(f"WARNING parsing {file_path} with esprima: {e} :: on line {last_frame.lineno} in {last_frame.filename}")
                    # Fall back to regex parsing for TypeScript files
                    logger.debug(f"Falling back to regex parsing for TypeScript file {file_path}")
                return []
        
        # Find Express.js route definitions
        self._find_express_routes(ast.body, endpoints, file_path)
        
        return endpoints
    
    def _find_express_routes(self, nodes, endpoints, file_path, router_var=None, mounts=None):
        """
        Recursively find Express.js route definitions in the AST.
        
        Args:
            nodes: List of AST nodes to search.
            endpoints: List to append found endpoints to.
            file_path: Path to the file being parsed.
            router_var: Name of the router variable, if known.
        """

        if mounts is None:
            mounts = {}
        
        for node in nodes:
            # Look for app.METHOD() or router.METHOD() calls
            if node.type == 'ExpressionStatement' and node.expression.type == 'CallExpression':
                call_expr = node.expression
                
                # Check if it's a method call on an object
                if call_expr.callee.type == 'MemberExpression':
                    obj = call_expr.callee.object
                    method = call_expr.callee.property.name.lower() if hasattr(call_expr.callee.property, 'name') else None

                    # Detect router.use('/base', someRouter) mounts to build prefixes
                    if method == 'use' and call_expr.arguments and len(call_expr.arguments) >= 2:
                        base_arg = call_expr.arguments[0]
                        router_arg = call_expr.arguments[1]
                        if (
                            getattr(base_arg, 'type', None) == 'Literal' and isinstance(getattr(base_arg, 'value', None), str)
                            and base_arg.value.startswith('/')
                        ):
                            # If the second argument is an identifier, use its name
                            if getattr(router_arg, 'type', None) == 'Identifier' and hasattr(router_arg, 'name'):
                                mounts[router_arg.name] = base_arg.value

                    # Check if it's a route method (get, post, put, delete, etc.)
                    if method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                        # Check if it's called on app, router, or a known router variable
                        obj_name = obj.name if hasattr(obj, 'name') else None
                        
                        if obj_name in ['app', 'router'] or obj_name == router_var or obj_name in mounts:
                            # Extract the route path from the first argument
                            if call_expr.arguments and len(call_expr.arguments) > 0:
                                path_arg = call_expr.arguments[0]
                                
                                # Extract the path string
                                path = None
                                if path_arg.type == 'Literal' and isinstance(path_arg.value, str):
                                    path = path_arg.value
                                
                                if path is not None and isinstance(path, str) and path.startswith('/'):
                                    # Apply mount prefix if applicable
                                    if obj_name in mounts:
                                        base = mounts[obj_name]
                                        if path == '/':
                                            path = base
                                        else:
                                            if base.endswith('/'):
                                                path = base.rstrip('/') + path
                                            else:
                                                path = base + path
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
                    self._find_express_routes(node.body, endpoints, file_path, router_var, mounts)
                elif hasattr(node.body, 'body') and isinstance(node.body.body, list):
                    self._find_express_routes(node.body.body, endpoints, file_path, router_var, mounts)
    
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
        # Capture the object name so we can apply mount prefixes if any
        express_route_pattern = r'([A-Za-z_$][A-Za-z0-9_$]*)\.(get|post|put|delete|patch|options|head)\s*\(\s*[\'\"](\/[^\'\"]*)[\'\"]'
        mount_use_pattern = r'[A-Za-z_$][A-Za-z0-9_$]*\.use\s*\(\s*[\'\"](\/[^\'\"]*)[\'\"]\s*,\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\)'

        # Build a list of mounted router variables to their base paths with line numbers
        mounts_list = []  # list of tuples: (var, base, line_no)
        for idx, line in enumerate(lines):
            m = re.search(mount_use_pattern, line)
            if m:
                base = m.group(1)
                var = m.group(2)
                mounts_list.append((var, base, idx + 1))
        
        # Find Express.js routes
        for i, line in enumerate(lines):
            for match in re.finditer(express_route_pattern, line):
                obj = match.group(1)
                method = match.group(2).upper()
                path = match.group(3)

                # Apply mount prefix if the object is a mounted router and the mount occurs before this line
                applicable_bases = [b for (v, b, ln) in mounts_list if v == obj and ln < (i + 1)]
                base = applicable_bases[-1] if applicable_bases else None
                if base:
                    if path == '/':
                        path = base
                    elif path.startswith('/'):
                        if base.endswith('/'):
                            path = base.rstrip('/') + path
                        else:
                            path = base + path
                
                endpoints.append({
                    "path": path,
                    "method": method,
                    "framework": "Express.js",
                    "file": file_path,
                    "line": i + 1,
                    "function": "anonymous",
                    "description": ""
                })
        
        # Detect frontend-style API wrappers like apiRequest({...})
        api_call_regex = re.compile(r"apiRequest\s*\(\s*\{(?P<body>.*?)\}\s*\)", re.DOTALL)
        for m in api_call_regex.finditer(content):
            body = m.group('body')
            api_match = re.search(r"\bapi\s*:\s*['\"]([^'\"]+)['\"]", body)
            path_match = re.search(r"\brequestPath\s*:\s*['\"]([^'\"]+)['\"]", body)
            method_match = re.search(r"\bconfig\s*:\s*\{[^}]*?\bmethod\s*:\s*['\"]([^'\"]+)['\"]", body, re.DOTALL)

            api_seg = api_match.group(1) if api_match else ''
            req_path = path_match.group(1) if path_match else ''
            method = (method_match.group(1) if method_match else 'get').upper()

            def norm(seg: str) -> str:
                return seg.strip('/')
            parts = []
            if api_seg:
                parts.append(norm(api_seg))
            if req_path:
                parts.append(norm(req_path))
            path = '/' + '/'.join([p for p in parts if p]) if parts else '/'

            start_idx = m.start()
            line_no = content.count('\n', 0, start_idx) + 1

            endpoints.append({
                "path": path,
                "method": method,
                "framework": "apiRequest",
                "file": file_path,
                "line": line_no,
                "function": "apiRequest",
                "description": ""
            })
        
        return endpoints