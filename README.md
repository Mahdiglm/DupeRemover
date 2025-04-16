<div align="center">
  <!-- PROJECT LOGO -->
  <a href="https://github.com/Mahdiglm/DupeRemover">
    <h1>🧹 DupeRemover</h1>
  </a>

  <h3>Efficient Duplicate Line Removal Tool for Large Text Files</h3>

  <!-- BADGES -->
  <p align="center">
    <a href="https://github.com/Mahdiglm/DupeRemover/releases"><img src="https://img.shields.io/badge/version-2.0.3-brightgreen.svg?style=for-the-badge" alt="Version"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.6+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge" alt="License"></a>
    <a href="#project-status"><img src="https://img.shields.io/badge/status-maintenance-yellow.svg?style=for-the-badge" alt="Status"></a>
    <a href="https://github.com/Mahdiglm/DupeRemover/stargazers"><img src="https://img.shields.io/github/stars/Mahdiglm/DupeRemover?style=for-the-badge" alt="Stars"></a>
  </p>
  
  <p>
    A powerful, high-performance CLI tool for removing duplicate lines from text files with advanced comparison options and parallel processing capabilities.
  </p>

  <!-- CALL TO ACTION BUTTONS -->
  <p>
    <a href="#installation" style="text-decoration: none;">
      <img src="https://img.shields.io/badge/Get_Started-4285F4?style=for-the-badge&logoColor=white" alt="Get Started">
    </a>
    <a href="#documentation" style="text-decoration: none;">
      <img src="https://img.shields.io/badge/Documentation-0078D4?style=for-the-badge&logoColor=white" alt="Documentation">
    </a>
    <a href="https://github.com/Mahdiglm/DupeRemover/issues" style="text-decoration: none;">
      <img src="https://img.shields.io/badge/Report_Bug-D42A36?style=for-the-badge&logoColor=white" alt="Report Bug">
    </a>
  </p>
</div>

<p align="center">
  <a href="#key-features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage-guide">Usage</a> •
  <a href="#benchmarks">Benchmarks</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

<hr>

## Overview

DupeRemover helps you eliminate duplicate content from text files while providing precise control over how duplicates are identified. Whether you're cleaning up log files, preparing datasets, or consolidating text content, DupeRemover offers a comprehensive and efficient solution.

**The Challenge:** Handling duplicate lines in large text files can be problematic, especially when:

- Files are too large for standard text editors (multi-GB files)
- You need fine-grained control over what constitutes a "duplicate"
- You need to process multiple files simultaneously
- You require detailed statistics about duplicate content

**Our Solution:** DupeRemover addresses these challenges with a powerful yet intuitive command-line interface, offering advanced features while maintaining ease of use.

## Key Features

### High Performance

- **Parallel processing** for multi-file operations
- **Chunked reading** for efficient handling of GB-size files
- **Optimized algorithms** for speed and memory efficiency

### Intelligent Processing

- **Six comparison modes** for versatile deduplication:
  - Case-sensitive/insensitive matching
  - Whitespace-insensitive detection
  - Content-hash for word order independence
  - Alphanumeric-only filtering
  - Fuzzy matching with adjustable similarity
- **Smart encoding detection** for various file formats

### Comprehensive Reporting

- **Multiple output formats**:
  - Text - Simple human-readable format
  - JSON - For programmatic processing
  - HTML - For visual presentation in browsers
  - CSV - For spreadsheet compatibility
  - XML - For structured data processing
  - YAML - For configuration-style output
  - Markdown - For documentation-friendly reports
- **Detailed statistics** on duplication rates
- **Visual progress tracking** during processing

### Safety Features

- **Backup creation** before modifications
- **Dry-run mode** for previewing changes
- **Comprehensive error handling** and logging

## Advanced Capabilities

<table>
  <tr>
    <th align="center" width="25%">Fuzzy Matching</th>
    <th align="center" width="25%">Parallel Processing</th>
    <th align="center" width="25%">Memory-Efficient Processing</th>
    <th align="center" width="25%">Real-time Streaming</th>
  </tr>
  <tr>
    <td>Identifies near-duplicate content using advanced similarity algorithms</td>
    <td>Processes multiple files simultaneously for maximum throughput</td>
    <td>Handles files of any size with constant memory usage</td>
    <td>Processes files in real-time as they are being written</td>
  </tr>
  <tr>
    <td align="center"><code>--mode fuzzy --similarity 0.8</code></td>
    <td align="center"><code>--parallel --workers 4</code></td>
    <td align="center"><code>--chunk-size 2097152</code></td>
    <td align="center"><code>--stream --follow</code></td>
  </tr>
</table>

## Comparison with Alternatives

<table>
  <tr>
    <th>Feature</th>
    <th>DupeRemover</th>
    <th>Standard Unix Tools</th>
    <th>Generic Text Editors</th>
  </tr>
  <tr>
    <td>Process GB-sized files</td>
    <td align="center">✓</td>
    <td align="center">✓</td>
    <td align="center">✗</td>
  </tr>
  <tr>
    <td>Multiple comparison modes</td>
    <td align="center">✓</td>
    <td align="center">Limited</td>
    <td align="center">✗</td>
  </tr>
  <tr>
    <td>Parallel processing</td>
    <td align="center">✓</td>
    <td align="center">✗</td>
    <td align="center">✗</td>
  </tr>
  <tr>
    <td>Detailed reports</td>
    <td align="center">✓</td>
    <td align="center">✗</td>
    <td align="center">✗</td>
  </tr>
  <tr>
    <td>Fuzzy matching</td>
    <td align="center">✓</td>
    <td align="center">✗</td>
    <td align="center">✗</td>
  </tr>
  <tr>
    <td>Progress tracking</td>
    <td align="center">✓</td>
    <td align="center">✗</td>
    <td align="center">✗</td>
  </tr>
</table>

## Installation

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

## Quick Start

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

## Usage Guide

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

# Exclude lines matching a pattern from deduplication
python main.py your_file.txt --exclude-pattern "^IMPORTANT:"

# Parallel processing with custom worker count
python main.py *.txt --parallel --workers 4

# Processing large files with custom chunk size (2MB)
python main.py large_file.txt --chunk-size 2097152
```

### Real-time Log Processing

DupeRemover can process log files in real-time as they're being written, removing duplicate entries on-the-fly:

```bash
# Basic streaming mode
python main.py server.log --stream --follow

# Stream with a 1-second polling interval
python main.py app.log --stream --follow --poll-interval 1.0

# Stream for a maximum of 3600 seconds (1 hour)
python main.py system.log --stream --follow --max-runtime 3600

# Customize the buffer size for recent lines
python main.py access.log --stream --follow --buffer-size 5000
```

#### Streaming Mode Options

| Option            | Description                                      | Default |
| :---------------- | :----------------------------------------------- | :------ |
| `--stream`        | Enable streaming mode                            | Off     |
| `--follow`        | Continue watching file for changes               | Off     |
| `--poll-interval` | Seconds between file checks in follow mode       | 0.5     |
| `--buffer-size`   | Maximum number of recent lines to keep in buffer | 10000   |
| `--max-runtime`   | Maximum runtime in seconds                       | None    |

### Output Options

```bash
# Save results to a different directory
python main.py your_file.txt -o output_directory/

# Generate an HTML report
python main.py your_file.txt --report html --report-file report.html

# Generate a CSV report for spreadsheet analysis
python main.py your_file.txt --report csv --report-file report.csv

# Generate an XML report for structured data
python main.py your_file.txt --report xml --report-file report.xml

# Generate a YAML report for configuration-style output
python main.py your_file.txt --report yaml --report-file report.yaml

# Generate a Markdown report for documentation
python main.py your_file.txt --report markdown --report-file report.md

# Enable colored output in text reports
python main.py your_file.txt --color

# Use quiet mode to suppress all non-error output
python main.py your_file.txt -q

# Save results and generate a JSON report
python main.py your_file.txt -o output_directory/ --report json --report-file report.json
```

### Safety Options

```bash
# Create backups before processing
python main.py your_file.txt --backup

# Create backups with custom extension
python main.py your_file.txt --backup --backup-ext .original

# Preserve file permissions when writing output files
python main.py your_file.txt --preserve-permissions

# Dry run - preview changes without modifying files
python main.py your_file.txt --dry-run

# Enable verbose logging
python main.py your_file.txt --verbose --log-file process.log
```

## Benchmarks

DupeRemover has been benchmarked for performance on various file sizes and configurations:

| File Size | Lines      | Duplicates | Mode               | Processing Time | Memory Usage |
| :-------- | :--------- | :--------- | :----------------- | :-------------- | :----------- |
| 10 MB     | 150,000    | 25%        | case-insensitive   | 0.8 seconds     | 15 MB        |
| 100 MB    | 1,500,000  | 30%        | case-insensitive   | 7.5 seconds     | 25 MB        |
| 1 GB      | 15,000,000 | 35%        | case-insensitive   | 76 seconds      | 35 MB        |
| 1 GB      | 15,000,000 | 35%        | fuzzy (0.8)        | 245 seconds     | 45 MB        |
| 1 GB      | 15,000,000 | 35%        | parallel (4 cores) | 25 seconds      | 120 MB       |

_Note: Benchmarks performed on a system with Intel i7-9700K, 32GB RAM, SSD storage._

## Example Output

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

## Use Cases

- **Log file analysis** - Clean up and deduplicate log files for better analysis
- **Data cleaning** - Preprocess datasets by removing duplicate entries
- **Text consolidation** - Merge multiple text files while removing duplicates
- **Code management** - Identify and remove duplicate strings or content
- **Document processing** - Clean up exported text data from PDFs or documents

## Real-World Showcase

DupeRemover has been successfully used in various environments:

- **Data Science Teams**: Preprocessing large datasets before analysis
- **DevOps Engineers**: Managing and cleaning log files from production systems
- **Content Managers**: Consolidating and deduplicating text content from multiple sources
- **Researchers**: Cleaning and preparing text corpora for analysis

## Documentation

For complete details on all available options:

```bash
python main.py --help
```

## Project Status

DupeRemover 2.0.3 is in **maintenance mode**. This means:

- The project has reached feature-complete status
- Bug fixes and minor improvements are still accepted
- No major new features are planned, but community contributions are welcome

## Contributing

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<hr>

<div align="center">
  <!-- PROJECT CONTACT AND SUPPORT LINKS -->
  <h3>Support & Contact</h3>
  <p>
    <a href="https://github.com/Mahdiglm/DupeRemover/issues">Report Bug</a> •
    <a href="https://github.com/Mahdiglm/DupeRemover/issues">Request Feature</a>
  </p>
  
  <p>
    <sub>Built with ❤️ by <a href="https://github.com/Mahdiglm">Mahdiglm</a></sub>
  </p>
</div>
