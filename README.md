<div align="center">
  <h1>🧹 DupeRemover</h1>

  <h3>Efficient Duplicate Line Removal Tool for Large Text Files</h3>

[![Version](https://img.shields.io/badge/version-2.0.1-brightgreen.svg?style=for-the-badge)](https://github.com/Mahdiglm/DupeRemover/releases)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/status-maintenance-yellow.svg?style=for-the-badge)]()
[![Stars](https://img.shields.io/github/stars/Mahdiglm/DupeRemover?style=for-the-badge)](https://github.com/Mahdiglm/DupeRemover/stargazers)

  <p>A powerful, high-performance CLI tool for removing duplicate lines from text files with advanced comparison options and parallel processing capabilities.</p>
</div>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage-guide">Usage Guide</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

<hr>

## 🌟 Key Features

### ⚡ High Performance

- **Parallel processing** for multi-file operations
- **Chunked reading** for efficient handling of GB-size files
- **Optimized algorithms** for speed and memory efficiency

### 🧠 Intelligent Processing

- **Six comparison modes** for versatile deduplication:
  - Case-sensitive/insensitive matching
  - Whitespace-insensitive detection
  - Content-hash for word order independence
  - Alphanumeric-only filtering
  - Fuzzy matching with adjustable similarity
- **Smart encoding detection** for various file formats

### 📊 Comprehensive Reporting

- **Multiple output formats** (Text, JSON, HTML)
- **Detailed statistics** on duplication rates
- **Visual progress tracking** during processing

### 🛡️ Safety Features

- **Backup creation** before modifications
- **Dry-run mode** for previewing changes
- **Comprehensive error handling** and logging

## 📥 Installation

### Prerequisites

- Python 3.6 or higher
- tqdm library

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/Mahdiglm/DupeRemover.git

# Navigate to the directory
cd DupeRemover

# Install required dependency
pip install tqdm
```

## 🚀 Quick Start

### Process a single file

```bash
python main.py your_file.txt
```

### Process multiple files

```bash
python main.py file1.txt file2.txt file3.txt
```

### Process all text files in a directory

```bash
python main.py -d your_directory/
```

## 📖 Usage Guide

### Input Options

| Option            | Description                                       |
| :---------------- | :------------------------------------------------ |
| `-d, --directory` | Process all text files in the specified directory |
| `-r, --recursive` | Recursively process directories                   |
| `--pattern`       | File pattern to match (default: \*.txt)           |

### Comparison Modes

| Mode                   | Command                         | Description                                    |
| :--------------------- | :------------------------------ | :--------------------------------------------- |
| Case-insensitive       | `--mode case-insensitive`       | Ignores case differences (default)             |
| Case-sensitive         | `--mode case-sensitive`         | Treats differently cased lines as unique       |
| Whitespace-insensitive | `--mode whitespace-insensitive` | Ignores all whitespace differences             |
| Content-hash           | `--mode content-hash`           | Ignores word order in lines                    |
| Alphanumeric-only      | `--mode alphanumeric-only`      | Ignores all non-alphanumeric characters        |
| Fuzzy                  | `--mode fuzzy`                  | Finds near-duplicate lines based on similarity |

### Advanced Processing

```bash
# Fuzzy matching with 70% similarity threshold
python main.py your_file.txt --mode fuzzy --similarity 0.7

# Parallel processing with custom worker count
python main.py *.txt --parallel --workers 4

# Processing large files with custom chunk size (2MB)
python main.py large_file.txt --chunk-size 2097152
```

### Output Options

```bash
# Save results to a different directory
python main.py your_file.txt -o output_directory/

# Generate an HTML report
python main.py your_file.txt --report html --report-file report.html

# Save results and generate a JSON report
python main.py your_file.txt -o output_directory/ --report json --report-file report.json
```

### Safety Options

```bash
# Create backups before processing
python main.py your_file.txt --backup

# Dry run - preview changes without modifying files
python main.py your_file.txt --dry-run

# Enable verbose logging
python main.py your_file.txt --verbose --log-file process.log
```

## 📊 Example Output

```
=== DupeRemover Results ===
Generated on: 2025-06-15 14:23:45

SUMMARY:
Files processed: 3/3
Files failed: 0
Total lines processed: 12,458
Total unique lines: 9,911
Total duplicates removed: 2,547
Overall duplication rate: 20.45%

DETAILS:
file1.txt:
  - Total lines: 5,621
  - Unique lines: 4,532
  - Duplicates removed: 1,089
  - Duplication rate: 19.37%
file2.txt:
  - Total lines: 3,542
  - Unique lines: 2,789
  - Duplicates removed: 753
  - Duplication rate: 21.26%
file3.txt:
  - Total lines: 3,295
  - Unique lines: 2,590
  - Duplicates removed: 705
  - Duplication rate: 21.40%

Processing completed in 3.24 seconds
```

## 💼 Use Cases

- **Log file analysis** - Clean up and deduplicate log files for better analysis
- **Data cleaning** - Preprocess datasets by removing duplicate entries
- **Text consolidation** - Merge multiple text files while removing duplicates
- **Code management** - Identify and remove duplicate strings or content
- **Document processing** - Clean up exported text data from PDFs or documents

## 📚 Documentation

For complete details on all available options:

```bash
python main.py --help
```

## 🛣️ Project Status

DupeRemover 2.0.1 is in **maintenance mode**. This means:

- The project has reached feature-complete status
- Bug fixes and minor improvements are still accepted
- No major new features are planned, but community contributions are welcome

## 👥 Contributing

We welcome contributions that improve stability, performance, or documentation. To contribute:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-improvement`)
3. Commit your changes (`git commit -m 'Add some amazing improvement'`)
4. Push to the branch (`git push origin feature/amazing-improvement`)
5. Open a Pull Request

Types of welcome contributions:

- Bug fixes
- Performance optimizations
- Platform compatibility improvements
- Documentation enhancements

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<hr>

<div align="center">
  <p>
    <sub>Built with ❤️ by <a href="https://github.com/Mahdiglm">Mahdiglm</a></sub>
  </p>
  
  <p>
    <a href="https://github.com/Mahdiglm/DupeRemover/issues">Report Bug</a> •
    <a href="https://github.com/Mahdiglm/DupeRemover/issues">Request Feature</a>
  </p>
</div>
