"""
Output formatting for Endpoint Finder.
"""

import os
import csv
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


def generate_report(results: Dict[str, Any], output_format: str = "text", output_file: Optional[str] = None) -> None:
    """
    Generate a report of the scan results.
    
    Args:
        results (Dict[str, Any]): Scan results.
        output_format (str): Output format (text, csv, json).
        output_file (str, optional): Path to output file. If not specified, output to console.
    """
    if output_format == "text":
        report = generate_text_report(results)
    elif output_format == "csv":
        report = generate_csv_report(results, output_file)
    elif output_format == "json":
        report = generate_json_report(results)
    else:
        logger.error(f"Unsupported output format: {output_format}")
        return
    
    if output_file:
        write_report_to_file(report, output_file, output_format)
    else:
        print(report)


def generate_text_report(results: Dict[str, Any]) -> str:
    """
    Generate a text report of the scan results.
    
    Args:
        results (Dict[str, Any]): Scan results.
        
    Returns:
        str: Text report.
    """
    report = []
    
    # Add header
    report.append("=" * 80)
    report.append("ENDPOINT FINDER SCAN RESULTS")
    report.append("=" * 80)
    report.append("")
    
    # Add summary
    report.append(f"Total repositories scanned: {results.get('total_repositories', 0)}")
    report.append(f"Total endpoints found: {results.get('total_endpoints', 0)}")
    report.append("")
    
    # Add language statistics
    if 'languages' in results:
        report.append("Language Statistics:")
        report.append("-" * 40)
        for language, stats in results['languages'].items():
            report.append(f"  {language}:")
            report.append(f"    Files scanned: {stats.get('files_scanned', 0)}")
            report.append(f"    Endpoints found: {stats.get('endpoints_found', 0)}")
        report.append("")
    
    # Add repository details
    if 'repositories' in results:
        for repo_idx, repo in enumerate(results['repositories']):
            report.append(f"Repository {repo_idx + 1}: {repo.get('repository', 'Unknown')}")
            report.append("-" * 80)
            
            if 'error' in repo:
                report.append(f"Error: {repo['error']}")
                report.append("")
                continue
            
            report.append(f"Endpoints found: {repo.get('endpoint_count', 0)}")
            report.append("")
            
            if repo.get('endpoints'):
                report.append("Endpoints:")
                for endpoint_idx, endpoint in enumerate(repo['endpoints']):
                    report.append(f"  {endpoint_idx + 1}. {endpoint.get('method', '')} {endpoint.get('path', '/')}")
                    report.append(f"     Framework: {endpoint.get('framework', 'Unknown')}")
                    report.append(f"     File: {endpoint.get('file', 'Unknown')}:{endpoint.get('line', 0)}")
                    report.append(f"     Function: {endpoint.get('function', 'unknown')}")
                    if endpoint.get('description'):
                        report.append(f"     Description: {endpoint.get('description')}")
                    report.append("")
            
            report.append("")
    
    return "\n".join(report)


def generate_csv_report(results: Dict[str, Any], output_file: Optional[str] = None) -> str:
    """
    Generate a CSV report of the scan results.
    
    Args:
        results (Dict[str, Any]): Scan results.
        output_file (str, optional): Path to output file.
        
    Returns:
        str: CSV report if output_file is None, otherwise empty string.
    """
    if not output_file:
        import io
        output = io.StringIO()
        writer = csv.writer(output)
    else:
        return ""  # Will write directly to file later
    
    # Write header
    header = ["Repository", "Path", "Method", "Framework", "File", "Line", "Function", "Description"]
    if not output_file:
        writer.writerow(header)
    
    # Write data
    rows = []
    if 'repositories' in results:
        for repo in results['repositories']:
            repo_name = repo.get('repository', 'Unknown')
            
            if 'error' in repo:
                rows.append([repo_name, "ERROR", "", "", "", "", "", repo['error']])
                continue
            
            if repo.get('endpoints'):
                for endpoint in repo['endpoints']:
                    rows.append([
                        repo_name,
                        endpoint.get('path', '/'),
                        endpoint.get('method', 'UNKNOWN'),
                        endpoint.get('framework', 'Unknown'),
                        endpoint.get('file', 'Unknown'),
                        endpoint.get('line', 0),
                        endpoint.get('function', 'unknown'),
                        endpoint.get('description', '')
                    ])
    
    if not output_file:
        for row in rows:
            writer.writerow(row)
        return output.getvalue()
    else:
        # Store rows for later writing
        return rows


def generate_json_report(results: Dict[str, Any]) -> str:
    """
    Generate a JSON report of the scan results.
    
    Args:
        results (Dict[str, Any]): Scan results.
        
    Returns:
        str: JSON report.
    """
    return json.dumps(results, indent=2)


def write_report_to_file(report, output_file: str, output_format: str) -> None:
    """
    Write a report to a file.
    
    Args:
        report: Report content.
        output_file (str): Path to output file.
        output_format (str): Output format.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        if output_format == "csv" and isinstance(report, list):
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(["Repository", "Path", "Method", "Framework", "File", "Line", "Function", "Description"])
                # Write data
                for row in report:
                    writer.writerow(row)
        else:
            with open(output_file, 'w') as f:
                f.write(report)
        
        logger.info(f"Report written to {output_file}")
    
    except Exception as e:
        logger.error(f"Error writing report to {output_file}: {e}")
        print(f"Error writing report to {output_file}: {e}")
        # Fall back to console output
        print(report if not isinstance(report, list) else "Error: Cannot display CSV report in console.")