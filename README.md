# 🧹 DupeRemover v2.0.0 (Final Release)

A powerful and flexible tool for removing duplicate lines from text files.

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-2.0.0-brightgreen.svg)
![Status](https://img.shields.io/badge/status-maintenance-yellow.svg)

## ✨ Features

- **Multiple comparison modes** - Remove duplicates based on different criteria
- **Parallel processing** - Process multiple files simultaneously for better performance
- **Memory optimization** - Process large files in chunks to minimize memory usage
- **Directory processing** - Process all text files in directories, optionally recursively
- **Preserves original order** - Keeps the first occurrence of each unique line
- **Multiple output formats** - Generate reports in text, JSON, or HTML
- **Smart encoding detection** - Automatically detect file encoding
- **Configurable output** - Save results to a different directory instead of overwriting
- **Progress tracking** - Visual progress bars for files and processing
- **Fuzzy matching** - Find near-duplicate lines with configurable similarity threshold
- **Backup creation** - Optional backups before modifying files
- **Dry run option** - See what would change without modifying files
- **Comprehensive CLI** - Easy to use with flexible options and argument groups
- **Thoroughly tested** - Reliable and stable operation

## 📢 Project Status

**DupeRemover 2.0.0 is the final planned major release.** The project has reached a feature-complete state with a comprehensive set of capabilities that should address most duplicate removal needs.

### Maintenance Mode

This project is now in maintenance mode, which means:

- No new major features are planned
- Bug fixes and minor improvements may still be accepted
- Community contributions are welcome

### Contributing

While active development has concluded, the project remains open to community contributions:

- **Bug fixes**: Corrections for any issues discovered
- **Performance improvements**: Optimizations that don't change the interface
- **Platform compatibility**: Updates to ensure compatibility with newer systems
- **Documentation**: Clarifications or additional examples

To contribute, please submit a pull request with a clear description of your changes and why they're beneficial.

## 📋 Requirements

- Python 3.6+
- tqdm library

## 🚀 Installation

1. Clone this repository or download the main script
2. Install the required dependency:

```bash
pip install tqdm
```

## 🔍 Basic Usage

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

### Process recursively with a specific pattern

```bash
python main.py -d your_directory/ -r --pattern "*.log"
```

## 🔧 Advanced Options

### Input Options

| Option            | Description                                       |
| ----------------- | ------------------------------------------------- |
| `-d, --directory` | Process all text files in the specified directory |
| `-r, --recursive` | Recursively process directories                   |
| `--pattern`       | File pattern to match (default: \*.txt)           |

### Comparison Options

| Mode                   | Flag                            | Description                                    |
| ---------------------- | ------------------------------- | ---------------------------------------------- |
| Case-insensitive       | `--mode case-insensitive`       | Ignores case differences (default)             |
| Case-sensitive         | `--mode case-sensitive`         | Treats differently cased lines as unique       |
| Whitespace-insensitive | `--mode whitespace-insensitive` | Ignores all whitespace differences             |
| Content-hash           | `--mode content-hash`           | Ignores word order in lines                    |
| Alphanumeric-only      | `--mode alphanumeric-only`      | Ignores all non-alphanumeric characters        |
| Fuzzy                  | `--mode fuzzy`                  | Finds near-duplicate lines based on similarity |

For fuzzy matching, you can set the similarity threshold:

```bash
python main.py your_file.txt --mode fuzzy --similarity 0.7
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

### Processing Options

```bash
# Process files in parallel
python main.py *.txt --parallel

# Specify number of worker processes
python main.py *.txt --parallel --workers 4

# Process in chunks of 2MB (for large files)
python main.py large_file.txt --chunk-size 2097152
```

### Other Options

```bash
# Create backups before processing
python main.py your_file.txt --backup

# Show progress
python main.py your_file.txt --progress

# Enable verbose logging to a file
python main.py your_file.txt --verbose --log-file process.log

# Dry run - don't make changes, just report
python main.py your_file.txt --dry-run
```

## 📊 Output Example

```
=== DupeRemover Results ===
Generated on: 2025-06-15 14:23:45

SUMMARY:
Files processed: 3/3
Files failed: 0
Total lines processed: 12458
Total unique lines: 9911
Total duplicates removed: 2547
Overall duplication rate: 20.45%

DETAILS:
file1.txt:
  - Total lines: 5621
  - Unique lines: 4532
  - Duplicates removed: 1089
  - Duplication rate: 19.37%
file2.txt:
  - Total lines: 3542
  - Unique lines: 2789
  - Duplicates removed: 753
  - Duplication rate: 21.26%
file3.txt:
  - Total lines: 3295
  - Unique lines: 2590
  - Duplicates removed: 705
  - Duplication rate: 21.40%

Processing completed in 3.24 seconds
```

## 🛠️ Super Advanced Usage

Combine multiple options for more power:

```bash
python main.py -d data/ -r --pattern "*.log" --mode fuzzy --similarity 0.75 \
  --parallel --workers 8 --chunk-size 4194304 --progress --backup \
  -o processed/ --report html --report-file report.html --log-file processing.log
```

This command will:

- Process all .log files in the data/ directory and subdirectories
- Use fuzzy matching with 75% similarity threshold
- Process files in parallel with 8 workers
- Use 4MB chunks for processing large files
- Show progress bars
- Create backups before processing
- Save results to the processed/ directory
- Generate an HTML report in report.html
- Save logs to processing.log

## ⚙️ Full Command-Line Help

```bash
python main.py --help
```

## 📝 License

MIT License

---

Made with ❤️ for efficient text processing
