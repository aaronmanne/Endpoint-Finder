# Endpoint Finder

A Python tool that scans GitHub repositories to identify API endpoints across various programming languages and frameworks. It helps developers discover and document API endpoints in codebases, which is useful for API documentation, security auditing, and understanding third-party APIs.

## Features

- **Repository Scanning**: Scan GitHub repositories by URL, username, or organization, or scan locally cloned repositories
- **Endpoint Identification**: Detect API endpoints in multiple programming languages and frameworks
- **Reporting**: Generate reports in various formats (text, CSV, JSON)
- **Language Support**:
  - **Tier 1** (Fully Implemented):
    - **Python**: Flask (`@app.route`, `app.get`, etc.), Django (`path`, `url`), FastAPI (`@app.get`, `@app.post`, etc.)
    - **JavaScript/Node.js**: Express.js (`app.get`, `router.post`, etc.)
    - **Java**: Spring Boot (`@RequestMapping`, `@GetMapping`, `@PostMapping`, etc.)
  - **Tier 2** (Planned):
    - **PHP**: Laravel, Symfony
    - **Ruby**: Rails
    - **Go**: Gin, Echo

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Install the base package
pip install endpoint-finder

# Install with optional parser dependencies for better accuracy
pip install endpoint-finder[parsers]

# Install with development dependencies (for contributing)
pip install endpoint-finder[dev]
```

### Option 2: Install from Source

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/endpoint-finder.git
   cd endpoint-finder
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   
   # Or with optional dependencies
   pip install -e ".[parsers,dev]"
   ```

## Usage

After installation, you can use Endpoint Finder either as a command-line tool or as a Python module.

### Command-Line Usage

#### Basic Usage

```bash
# If installed via pip
endpoint-finder scan --repo https://github.com/username/repo

# If using the module directly
python -m endpoint_finder scan --repo https://github.com/username/repo
```

#### Scan Multiple Repositories

```bash
endpoint-finder scan --repo https://github.com/username/repo1 https://github.com/username/repo2
```

#### Scan All Repositories from a User or Organization

```bash
# Scan all public repositories from a user
endpoint-finder scan --user username

# Scan all public repositories from an organization
endpoint-finder scan --org organization
```

#### Scan Local Repositories

```bash
# Scan a single local repository
endpoint-finder scan --local /path/to/local/repo

# Scan multiple local repositories
endpoint-finder scan --local /path/to/repo1 /path/to/repo2
```

#### Filter by Language

```bash
# Scan only Python and JavaScript files
endpoint-finder scan --repo https://github.com/username/repo --languages python javascript
```

#### Output Options

```bash
# Output to console (default)
endpoint-finder scan --repo https://github.com/username/repo

# Output to CSV file
endpoint-finder scan --repo https://github.com/username/repo --output csv --output-file results.csv

# Output to JSON file
endpoint-finder scan --repo https://github.com/username/repo --output json --output-file results.json
```

#### Authentication

For private repositories or to avoid GitHub API rate limits:

```bash
endpoint-finder scan --repo https://github.com/username/repo --token YOUR_GITHUB_TOKEN
```

### Python Module Usage

You can also use Endpoint Finder as a Python module in your own scripts:

```python
from endpoint_finder.scanner import scan_repositories

# Scan a remote GitHub repository
results = scan_repositories(
    repositories=["https://github.com/username/repo"],
    config={
        "github": {"token": "YOUR_GITHUB_TOKEN"},
        "scan": {"languages": ["python", "javascript", "java"]},
        "output": {"format": "json"}
    }
)

# Scan a local repository
results = scan_repositories(
    repositories=[],
    config={
        "scan": {"languages": ["python", "javascript", "java"]},
        "output": {"format": "json"}
    },
    local_repos=["/path/to/local/repo"]
)

# Process the results
print(f"Found {results['total_endpoints']} endpoints")
for repo in results['repositories']:
    print(f"Repository: {repo['repository']}")
    print(f"Endpoints: {repo['endpoint_count']}")
    for endpoint in repo['endpoints']:
        print(f"  {endpoint['method']} {endpoint['path']}")
```

## Configuration

You can use a configuration file to set default options:

```bash
endpoint-finder scan --config config.yaml
```

Example `config.yaml`:

```yaml
# GitHub API configuration
github:
  # GitHub personal access token (optional)
  token: YOUR_GITHUB_TOKEN
  
  # GitHub username to scan repositories from (optional)
  # user: username
  
  # GitHub organization to scan repositories from (optional)
  # org: organization

# Scanning configuration
scan:
  # Languages to scan for endpoints
  languages:
    - python    # Flask, Django, FastAPI
    - javascript # Express.js
    - java      # Spring Boot
  
  # Directories to exclude from scanning
  exclude_dirs:
    - .git
    - node_modules
    - venv
    - .venv
    - __pycache__

# Output configuration
output:
  # Output format: text, csv, or json
  format: json
  
  # Output file (optional)
  file: results.json
```

A sample configuration file is included in the repository as `config.example.yaml`.

## Contributing

Contributions are welcome! Here's how you can help:

1. **Add support for new frameworks**: Implement parsers for additional frameworks and languages.
2. **Improve existing parsers**: Enhance the accuracy and coverage of existing parsers.
3. **Add features**: Implement new features like parallel processing, caching, or a web interface.
4. **Fix bugs**: Help fix issues and improve the codebase.
5. **Improve documentation**: Enhance the documentation with examples and tutorials.

### Development Setup

1. Fork and clone the repository
2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[parsers,dev]"
   ```
4. Run tests:
   ```bash
   pytest
   ```

### Adding a New Parser

To add support for a new framework:

1. Create a new file in the `endpoint_finder/parsers` directory (e.g., `ruby.py`)
2. Implement a parser class that extends `BaseParser`
3. Register your parser in `endpoint_finder/parsers/__init__.py`
4. Add tests in the `tests` directory
5. Update the documentation

## License

MIT