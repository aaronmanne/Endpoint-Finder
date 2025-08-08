#!/usr/bin/env python3
"""
Main entry point for the Endpoint Finder tool.
"""

import argparse
import sys
from endpoint_finder.scanner import scan_repositories
from endpoint_finder.config import load_config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan GitHub repositories to identify API endpoints."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan repositories for API endpoints")
    repo_group = scan_parser.add_mutually_exclusive_group(required=True)
    repo_group.add_argument("--repo", nargs="+", help="GitHub repository URLs to scan")
    repo_group.add_argument("--local", nargs="+", help="Local repository paths to scan")
    repo_group.add_argument("--user", help="GitHub username to scan repositories from")
    repo_group.add_argument("--org", help="GitHub organization to scan repositories from")
    
    scan_parser.add_argument("--token", help="GitHub personal access token")
    scan_parser.add_argument("--config", help="Path to configuration file")
    scan_parser.add_argument(
        "--output", 
        choices=["text", "csv", "json"], 
        default="text",
        help="Output format (default: text)"
    )
    scan_parser.add_argument(
        "--output-file", 
        help="Path to output file (if not specified, output to console)"
    )
    scan_parser.add_argument(
        "--languages",
        nargs="+",
        choices=["python", "javascript", "java", "php", "ruby", "go"],
        help="Languages to scan for (default: all supported languages)"
    )
    
    # OpenAPI/Swagger options
    openapi_group = scan_parser.add_argument_group("OpenAPI/Swagger Options")
    openapi_group.add_argument(
        "--find-openapi",
        action="store_true",
        help="Find existing OpenAPI/Swagger documentation (default: enabled)"
    )
    openapi_group.add_argument(
        "--no-find-openapi",
        action="store_true",
        help="Disable finding existing OpenAPI/Swagger documentation"
    )
    openapi_group.add_argument(
        "--generate-openapi",
        action="store_true",
        help="Generate OpenAPI documentation if none exists (default: enabled)"
    )
    openapi_group.add_argument(
        "--no-generate-openapi",
        action="store_true",
        help="Disable generating OpenAPI documentation"
    )
    openapi_group.add_argument(
        "--openapi-dir",
        help="Directory to save OpenAPI documentation (default: openapi-docs)"
    )
    openapi_group.add_argument(
        "--openapi-format",
        choices=["json", "yaml"],
        default="json",
        help="Format for generated OpenAPI documentation (default: json)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()
    
    if not args.command:
        print("Error: No command specified. Use 'scan' to scan repositories.")
        sys.exit(1)
    
    if args.command == "scan":
        config = {}
        if args.config:
            config = load_config(args.config)
        
        # Override config with command line arguments
        if args.token:
            config["github"] = config.get("github", {})
            config["github"]["token"] = args.token
        
        if args.languages:
            config["scan"] = config.get("scan", {})
            config["scan"]["languages"] = args.languages
        
        if args.output:
            config["output"] = config.get("output", {})
            config["output"]["format"] = args.output
        
        if args.output_file:
            config["output"] = config.get("output", {})
            config["output"]["file"] = args.output_file
            
        # Process OpenAPI options
        config["openapi"] = config.get("openapi", {})
        
        # Handle find_existing option
        if args.find_openapi:
            config["openapi"]["find_existing"] = True
        elif args.no_find_openapi:
            config["openapi"]["find_existing"] = False
            
        # Handle generate_if_none option
        if args.generate_openapi:
            config["openapi"]["generate_if_none"] = True
        elif args.no_generate_openapi:
            config["openapi"]["generate_if_none"] = False
            
        # Handle output directory and format
        if args.openapi_dir:
            config["openapi"]["output_dir"] = args.openapi_dir
        if args.openapi_format:
            config["openapi"]["output_format"] = args.openapi_format
        
        # Determine repositories to scan
        repositories = []
        local_repos = []
        
        if args.repo:
            repositories = args.repo
        elif args.local:
            local_repos = args.local
        elif args.user:
            # This will be implemented in the github module
            config["github"] = config.get("github", {})
            config["github"]["user"] = args.user
        elif args.org:
            # This will be implemented in the github module
            config["github"] = config.get("github", {})
            config["github"]["org"] = args.org
        
        # Run the scan
        scan_repositories(repositories, config, local_repos=local_repos)


if __name__ == "__main__":
    main()