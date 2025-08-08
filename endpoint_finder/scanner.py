"""
Repository scanning functionality for Endpoint Finder.
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional

from git import Repo, GitCommandError
from tqdm import tqdm

from endpoint_finder.github import get_repositories
from endpoint_finder.parsers import get_parser_for_language
from endpoint_finder.output import generate_report
from endpoint_finder.openapi import (
    find_openapi_files, 
    save_openapi_file, 
    generate_openapi_spec, 
    save_generated_openapi
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def clone_repository(repo_url: str, token: Optional[str] = None) -> str:
    """
    Clone a repository to a temporary directory.
    
    Args:
        repo_url (str): URL of the repository to clone.
        token (str, optional): GitHub personal access token for private repositories.
        
    Returns:
        str: Path to the cloned repository.
        
    Raises:
        GitCommandError: If the repository cannot be cloned.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="endpoint-finder-")
    
    try:
        # Modify URL to include token if provided
        clone_url = repo_url
        if token and "github.com" in repo_url:
            # Insert token into URL
            if repo_url.startswith("https://"):
                clone_url = f"https://{token}@{repo_url[8:]}"
        
        # Clone the repository
        logger.info(f"Cloning repository: {repo_url}")
        Repo.clone_from(clone_url, temp_dir)
        return temp_dir
    
    except GitCommandError as e:
        logger.error(f"Failed to clone repository {repo_url}: {e}")
        raise


def scan_repository(repo_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan a repository for API endpoints and OpenAPI/Swagger documentation.
    
    Args:
        repo_path (str): Path to the repository.
        config (Dict[str, Any]): Configuration dictionary.
        
    Returns:
        Dict[str, Any]: Dictionary containing the scan results.
    """
    logger.info(f"Scanning repository at {repo_path}")
    
    # Get languages to scan
    languages = config.get("scan", {}).get("languages", ["python", "javascript", "java"])
    exclude_dirs = config.get("scan", {}).get("exclude_dirs", [])
    
    # Get OpenAPI configuration
    openapi_config = config.get("openapi", {})
    find_existing = openapi_config.get("find_existing", True)
    generate_if_none = openapi_config.get("generate_if_none", True)
    output_dir = openapi_config.get("output_dir", "openapi-docs")
    output_format = openapi_config.get("output_format", "json")
    
    # Initialize results
    results = {
        "repository": os.path.basename(repo_path),
        "endpoints": [],
        "endpoint_count": 0,
        "languages": {},
        "openapi": {
            "existing_files": [],
            "generated_file": None
        }
    }
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)

            # Skip files in common source library directories
            if any(part in file_path.lower() for part in ['node_modules', 'vendor', 'third_party', 'lib', 'libs']):
                continue

            # Determine file language based on extension
            file_ext = os.path.splitext(file)[1].lower()
            language = None
            
            if file_ext in ['.py']:
                language = 'python'
            elif file_ext in ['.js', '.jsx', '.ts', '.tsx']:
                language = 'javascript'
            elif file_ext in ['.java']:
                language = 'java'
            elif file_ext in ['.php']:
                language = 'php'
            elif file_ext in ['.rb']:
                language = 'ruby'
            elif file_ext in ['.go']:
                language = 'go'
            
            # Skip if language not in the list to scan
            if not language or language not in languages:
                continue
            
            # Get parser for the language
            parser = get_parser_for_language(language)
            if not parser:
                logger.warning(f"No parser available for {language}")
                continue
            
            # Parse the file for endpoints
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                file_endpoints = parser.parse(content, rel_path)
                
                # Add endpoints to results
                if file_endpoints:
                    results["endpoints"].extend(file_endpoints)
                    
                    # Update language statistics
                    if language not in results["languages"]:
                        results["languages"][language] = {
                            "files_scanned": 0,
                            "endpoints_found": 0
                        }
                    
                    results["languages"][language]["files_scanned"] += 1
                    results["languages"][language]["endpoints_found"] += len(file_endpoints)
            except IndexError as e:
                logger.debug(f"IndexError parsing file {rel_path}: {e}")
            except Exception as e:
                logger.error(f"Error parsing file {rel_path}: {e}")
    
    # Update endpoint count
    results["endpoint_count"] = len(results["endpoints"])
    
    # Find existing OpenAPI/Swagger documentation
    if find_existing:
        logger.info("Searching for existing OpenAPI/Swagger documentation")
        openapi_files = find_openapi_files(repo_path)
        
        if openapi_files:
            logger.info(f"Found {len(openapi_files)} OpenAPI/Swagger files")
            results["openapi"]["existing_files"] = openapi_files
            
            # Save found OpenAPI files
            saved_files = []
            for openapi_file in openapi_files:
                try:
                    saved_path = save_openapi_file(openapi_file, output_dir)
                    saved_files.append({
                        "original": openapi_file["file"],
                        "saved": saved_path
                    })
                except Exception as e:
                    logger.error(f"Error saving OpenAPI file {openapi_file['file']}: {e}")
            
            results["openapi"]["saved_files"] = saved_files
    
    # Generate OpenAPI documentation if none exists and there are endpoints
    if generate_if_none and not results["openapi"]["existing_files"] and results["endpoints"]:
        logger.info("No existing OpenAPI documentation found, generating from endpoints")
        try:
            # Generate OpenAPI specification
            spec = generate_openapi_spec(
                results["endpoints"], 
                results["repository"],
                output_format
            )
            
            # Save generated specification
            saved_path = save_generated_openapi(
                spec, 
                output_dir, 
                results["repository"],
                output_format
            )
            
            results["openapi"]["generated_file"] = saved_path
            logger.info(f"Generated OpenAPI documentation saved to {saved_path}")
        except Exception as e:
            logger.error(f"Error generating OpenAPI documentation: {e}")
    
    return results


def scan_repositories(repositories: List[str], config: Dict[str, Any], local_repos: List[str] = None) -> Dict[str, Any]:
    """
    Scan multiple repositories for API endpoints.
    
    Args:
        repositories (List[str]): List of repository URLs to scan.
        config (Dict[str, Any]): Configuration dictionary.
        local_repos (List[str], optional): List of local repository paths to scan.
        
    Returns:
        Dict[str, Any]: Dictionary containing the scan results.
    """
    # Initialize local_repos if not provided
    if local_repos is None:
        local_repos = []
        
    # If repositories list is empty, try to get repositories from GitHub
    if not repositories and not local_repos:
        github_config = config.get("github", {})
        user = github_config.get("user")
        org = github_config.get("org")
        token = github_config.get("token")
        
        if user:
            repositories = get_repositories(user=user, token=token)
        elif org:
            repositories = get_repositories(org=org, token=token)
    
    if not repositories and not local_repos:
        logger.error("No repositories specified for scanning")
        return {"error": "No repositories specified for scanning"}
    
    # Initialize results
    results = {
        "repositories": [],
        "total_repositories": len(repositories) + len(local_repos),
        "total_endpoints": 0,
        "languages": {}
    }
    
    # Scan remote repositories
    for repo_url in tqdm(repositories, desc="Scanning remote repositories"):
        try:
            # Clone the repository
            token = config.get("github", {}).get("token")
            repo_path = clone_repository(repo_url, token)
            
            # Scan the repository
            repo_results = scan_repository(repo_path, config)
            
            # Add to overall results
            results["repositories"].append(repo_results)
            results["total_endpoints"] += repo_results["endpoint_count"]
            
            # Update language statistics
            for language, stats in repo_results["languages"].items():
                if language not in results["languages"]:
                    results["languages"][language] = {
                        "files_scanned": 0,
                        "endpoints_found": 0
                    }
                
                results["languages"][language]["files_scanned"] += stats["files_scanned"]
                results["languages"][language]["endpoints_found"] += stats["endpoints_found"]
            
        except Exception as e:
            logger.error(f"Error scanning repository {repo_url}: {e}")
            results["repositories"].append({
                "repository": repo_url,
                "error": str(e),
                "endpoints": [],
                "endpoint_count": 0
            })
    
    # Scan local repositories
    for repo_path in tqdm(local_repos, desc="Scanning local repositories"):
        try:
            # Verify the path exists
            if not os.path.isdir(repo_path):
                raise ValueError(f"Path is not a valid directory: {repo_path}")
                
            # Scan the repository
            repo_results = scan_repository(repo_path, config)
            
            # Add to overall results
            results["repositories"].append(repo_results)
            results["total_endpoints"] += repo_results["endpoint_count"]
            
            # Update language statistics
            for language, stats in repo_results["languages"].items():
                if language not in results["languages"]:
                    results["languages"][language] = {
                        "files_scanned": 0,
                        "endpoints_found": 0
                    }
                
                results["languages"][language]["files_scanned"] += stats["files_scanned"]
                results["languages"][language]["endpoints_found"] += stats["endpoints_found"]
            
        except Exception as e:
            logger.error(f"Error scanning local repository {repo_path}: {e}")
            results["repositories"].append({
                "repository": repo_path,
                "error": str(e),
                "endpoints": [],
                "endpoint_count": 0
            })
    
    # Generate report
    output_config = config.get("output", {})
    output_format = output_config.get("format", "text")
    output_file = output_config.get("file")
    
    generate_report(results, output_format, output_file)
    
    return results