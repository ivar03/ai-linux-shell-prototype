# AI Shell CLI - Setup Script

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "AI-native Linux CLI tool that converts natural language to commands"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    # Fallback requirements if file doesn't exist
    requirements = [
        "click>=8.0.0",
        "rich>=12.0.0",
        "ollama>=0.1.0",
        "psutil>=5.9.0",
        "requests>=2.28.0",
        "typing-extensions>=4.0.0"
    ]

setup(
    name="aishell",
    version="0.1.0",
    description="AI-native Linux CLI tool that converts natural language queries to commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ravi k banchhiwal",
    author_email="<todo>",
    url="<todo>",
    
    # Package configuration
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=requirements,
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "sqlite": [
            "sqlite3",  # Usually built-in but explicit for clarity
        ],
        "advanced": [
            "numpy>=1.21.0",
            "pandas>=1.3.0",
            "matplotlib>=3.5.0",
        ]
    },
    
    # Entry points for CLI
    entry_points={
        "console_scripts": [
            "aishell=aishell:main",
            "ais=aishell:main",  # Short alias
        ],
    },
    
    # Package metadata
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Shells",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Console",
    ],
    
    keywords=[
        "ai", "cli", "shell", "linux", "natural-language", "command-line",
        "automation", "llm", "ollama", "terminal", "productivity"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "<todo>",
        "Source": "<todo>",
        "Documentation": "<todo>",
        "Funding": "<todo>",
    },
    
    # Package data
    package_data={
        "aishell": [
            "data/*.json",
            "templates/*.txt",
            "docs/*.md",
        ],
    },
    
    # Additional files to include
    data_files=[
        ("share/aishell", ["README.md", "LICENSE"]),
        ("share/aishell/examples", ["examples/basic_usage.md"]),
    ],
    
    # Zip safe
    zip_safe=False,
    
    # Platform specific
    platforms=["linux", "darwin"],  # Linux and macOS
    
    # Command line interface
    scripts=[],  # Using entry_points instead
)

# Post-install message
print("""
🤖 AI Shell CLI installed successfully!

Quick start:
1. Make sure Ollama is running: ollama serve
2. Pull a model: ollama pull llama3.2:3b
3. Try it: aishell "show files larger than 1GB"

For help: aishell --help
For logs: aishell logs
For history: aishell history

Happy commanding! 🚀
""")