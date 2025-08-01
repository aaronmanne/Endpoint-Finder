"""
Base parser class for detecting API endpoints.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    """
    Base class for language-specific parsers.
    """
    
    @abstractmethod
    def parse(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a file for API endpoints.
        
        Args:
            content (str): Content of the file to parse.
            file_path (str): Path to the file being parsed.
            
        Returns:
            List[Dict[str, Any]]: List of endpoints found in the file.
            Each endpoint is a dictionary with at least the following keys:
            - path: The URL path of the endpoint.
            - method: The HTTP method (GET, POST, etc.).
            - file: The file where the endpoint was found.
            - line: The line number where the endpoint was found.
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement parse method")