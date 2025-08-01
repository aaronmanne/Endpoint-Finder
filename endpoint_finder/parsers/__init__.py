"""
Language-specific parsers for detecting API endpoints.
"""

import logging
from typing import Dict, Optional

from endpoint_finder.parsers.base import BaseParser
from endpoint_finder.parsers.python import PythonParser
from endpoint_finder.parsers.javascript import JavaScriptParser
from endpoint_finder.parsers.java import JavaParser

# Configure logging
logger = logging.getLogger(__name__)

# Registry of parsers
_PARSERS: Dict[str, BaseParser] = {
    "python": PythonParser(),
    "javascript": JavaScriptParser(),
    "java": JavaParser(),
}


def get_parser_for_language(language: str) -> Optional[BaseParser]:
    """
    Get a parser for the specified language.
    
    Args:
        language (str): Language to get a parser for.
        
    Returns:
        Optional[BaseParser]: Parser for the language, or None if no parser is available.
    """
    parser = _PARSERS.get(language.lower())
    if not parser:
        logger.warning(f"No parser available for language: {language}")
    return parser


def register_parser(language: str, parser: BaseParser) -> None:
    """
    Register a parser for a language.
    
    Args:
        language (str): Language to register the parser for.
        parser (BaseParser): Parser to register.
    """
    _PARSERS[language.lower()] = parser
    logger.info(f"Registered parser for language: {language}")