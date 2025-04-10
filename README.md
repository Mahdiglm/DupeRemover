# 🧹 DupeRemover

A powerful and flexible tool for removing duplicate lines from text files.

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- **Multiple comparison modes** - Remove duplicates based on different criteria
- **Preserves original order** - Keeps the first occurrence of each unique line
- **Progress tracking** - Visual progress bar for large files
- **Backup creation** - Optional backups before modifying files
- **Multiple file support** - Process several files in one command
- **Command-line interface** - Easy to use with flexible options

## 📋 Requirements

- Python 3.6+
- tqdm library

## 🚀 Installation

1. Clone this repository or download the main script
2. Install the required dependency:

```bash
pip install tqdm
```

## 🔍 Usage

### Basic usage

```bash
python main.py your_file.txt
```

### Process multiple files

```bash
python main.py file1.txt file2.txt file3.txt
```

### Create backups before processing

```bash
python main.py your_file.txt --backup
# or
python main.py your_file.txt -b
```

### Show progress bar for large files

```bash
python main.py your_file.txt --progress
# or
python main.py your_file.txt -p
```

### Enable verbose logging

```bash
python main.py your_file.txt --verbose
# or
python main.py your_file.txt -v
```

### Get help

```bash
python main.py --help
```

## 🔄 Comparison Modes

| Mode                   | Flag                            | Description                              |
| ---------------------- | ------------------------------- | ---------------------------------------- |
| Case-insensitive       | `--mode case-insensitive`       | Ignores case differences (default)       |
| Case-sensitive         | `--mode case-sensitive`         | Treats differently cased lines as unique |
| Whitespace-insensitive | `--mode whitespace-insensitive` | Ignores all whitespace differences       |

Example:

```bash
python main.py your_file.txt --mode case-sensitive
# or
python main.py your_file.txt -m whitespace-insensitive
```

## 📊 Output Example

```
SUMMARY:
Files processed: 3/3
Total duplicates removed: 2547
Comparison mode: case-insensitive
```

## 🛠️ Advanced Usage

Combine options for more power:

```bash
python main.py *.txt -m whitespace-insensitive -b -p -v
```

This command will:

- Process all text files in the current directory
- Use whitespace-insensitive comparison
- Create backups of all files
- Show progress bars
- Display verbose logging

## 📝 License

MIT License

---

Made with ❤️ for efficient text processing
