"""
GitHub API integration for Endpoint Finder.
"""

import logging
from typing import List, Optional

from github import Github, GithubException

# Configure logging
logger = logging.getLogger(__name__)


def get_repositories(user: Optional[str] = None, org: Optional[str] = None, token: Optional[str] = None) -> List[str]:
    """
    Get a list of repository URLs from a GitHub user or organization.
    
    Args:
        user (str, optional): GitHub username.
        org (str, optional): GitHub organization name.
        token (str, optional): GitHub personal access token.
        
    Returns:
        List[str]: List of repository URLs.
        
    Raises:
        ValueError: If neither user nor org is provided.
        GithubException: If there is an error accessing the GitHub API.
    """
    if not user and not org:
        raise ValueError("Either user or org must be provided")
    
    # Initialize GitHub API client
    g = Github(token) if token else Github()
    
    try:
        repositories = []
        
        if user:
            logger.info(f"Getting repositories for user: {user}")
            user_obj = g.get_user(user)
            repos = user_obj.get_repos()
        else:
            logger.info(f"Getting repositories for organization: {org}")
            org_obj = g.get_organization(org)
            repos = org_obj.get_repos()
        
        # Extract repository URLs
        for repo in repos:
            if not repo.private or token:
                repositories.append(repo.clone_url)
        
        logger.info(f"Found {len(repositories)} repositories")
        return repositories
    
    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        raise


def search_repositories(query: str, token: Optional[str] = None) -> List[str]:
    """
    Search for repositories on GitHub.
    
    Args:
        query (str): Search query.
        token (str, optional): GitHub personal access token.
        
    Returns:
        List[str]: List of repository URLs.
        
    Raises:
        GithubException: If there is an error accessing the GitHub API.
    """
    # Initialize GitHub API client
    g = Github(token) if token else Github()
    
    try:
        logger.info(f"Searching for repositories with query: {query}")
        repositories = []
        
        # Search for repositories
        repos = g.search_repositories(query=query)
        
        # Extract repository URLs
        for repo in repos:
            if not repo.private or token:
                repositories.append(repo.clone_url)
        
        logger.info(f"Found {len(repositories)} repositories")
        return repositories
    
    except GithubException as e:
        logger.error(f"GitHub API error: {e}")
        raise