from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="endpoint-finder",
    version="0.1.0",
    author="Endpoint Finder Team",
    author_email="example@example.com",
    description="A tool to scan GitHub repositories and identify API endpoints",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/endpoint-finder",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.28.0",
        "GitPython>=3.1.30",
        "PyGithub>=1.58.0",
        "PyYAML>=6.0",
        "tqdm>=4.65.0",
        "colorama>=0.4.6",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "flake8>=5.0.0",
            "black>=22.0.0",
        ],
        "parsers": [
            "ast-comments>=1.0.1",
            "esprima>=4.0.1",
            "javalang>=0.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "endpoint-finder=endpoint_finder.__main__:main",
        ],
    },
)