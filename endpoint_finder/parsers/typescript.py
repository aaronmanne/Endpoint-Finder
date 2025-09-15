"""
TypeScript parser for detecting API endpoints in Express.js applications.

This parser focuses on identifying common Express-style route declarations
within TypeScript (.ts/.tsx) source files. It uses a lightweight regex-based
approach to avoid requiring a TS AST parser dependency.
"""

import logging
import re
from typing import List, Dict, Any

from endpoint_finder.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class TypeScriptParser(BaseParser):
    """
    Parser for TypeScript files to detect API endpoints (Express.js style).
    """

    def parse(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a TypeScript file for API endpoints.

        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.

        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        # For TypeScript, we can optionally strip simple type annotations to
        # reduce false negatives, but our regex targets call expressions and
        # shouldn't be impacted much. We'll proceed directly with regex.
        return self._parse_with_regex(content, file_path)

    def _parse_with_regex(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a TypeScript file for API endpoints using regular expressions.

        Supports patterns such as:
          - app.get('/path', handler)
          - router.post("/path", handler)
          - someRouter.use('/base', otherRouter)
          - apiRequest({ api: 'segment', requestPath: 'resource', config: { method: 'get' } })

        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
        """
        endpoints: List[Dict[str, Any]] = []

        # Split content into lines for line number tracking
        lines = content.split('\n')

        # Express-like route patterns
        # Matches identifiers like app, router, or any variable name
        # Capture the object name so we can apply mount prefixes if any
        express_route_pattern = r"([A-Za-z_$][A-Za-z0-9_$]*)\.(get|post|put|delete|patch|options|head)\s*\(\s*['\"](\/[^'\"]*)['\"]"
        mount_use_pattern = r"[A-Za-z_$][A-Za-z0-9_$]*\.use\s*\(\s*['\"](\/[^'\"]*)['\"]\s*,\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\)"

        # Build a list of mounted router variables to their base paths with line numbers
        mounts_list = []  # list of tuples: (var, base, line_no)
        for idx, line in enumerate(lines):
            m = re.search(mount_use_pattern, line)
            if m:
                base = m.group(1)
                var = m.group(2)
                mounts_list.append((var, base, idx + 1))

        route_regex = re.compile(express_route_pattern)

        for i, line in enumerate(lines):
            for match in route_regex.finditer(line):
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
        # Capture object body inside apiRequest({...}) even across multiple lines
        api_call_regex = re.compile(r"apiRequest\s*\(\s*\{(?P<body>.*?)\}\s*\)", re.DOTALL)
        for m in api_call_regex.finditer(content):
            body = m.group('body')
            # Extract api segment and requestPath
            api_match = re.search(r"\bapi\s*:\s*['\"]([^'\"]+)['\"]", body)
            path_match = re.search(r"\brequestPath\s*:\s*['\"]([^'\"]+)['\"]", body)
            # Extract HTTP method from nested config
            method_match = re.search(r"\bconfig\s*:\s*\{[^}]*?\bmethod\s*:\s*['\"]([^'\"]+)['\"]", body, re.DOTALL)

            api_seg = api_match.group(1) if api_match else ''
            req_path = path_match.group(1) if path_match else ''
            method = (method_match.group(1) if method_match else 'get').upper()

            # Build full path
            def norm(seg: str) -> str:
                return seg.strip('/')

            parts = []
            if api_seg:
                parts.append(norm(api_seg))
            if req_path:
                parts.append(norm(req_path))
            path = '/' + '/'.join([p for p in parts if p]) if parts else '/'

            # Compute line number where the apiRequest starts
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
