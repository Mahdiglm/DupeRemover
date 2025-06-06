"""
duplicate_remover.py - Removes duplicates from text files with various comparison options.
Supports multiple files, progress tracking, and backup creation.
Version 2.0.4 - Stable release with exclude pattern functionality.
"""

import os
import sys
import logging
import argparse
import shutil
import re
import concurrent.futures
import hashlib
import itertools
from typing import List, Set, Dict, Tuple, Generator, Any, Optional, Union
from tqdm import tqdm
from pathlib import Path
import threading
import time
import signal
from datetime import datetime
import json
import csv

# Version information
__version__ = "2.0.4"


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Configure the logging system."""
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, mode='w')
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Could not create log file: {e}")
    
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )


def chunk_reader(file_path: str, chunk_size: int = 1024*1024) -> Generator[List[str], None, None]:
    """
    Read a file in chunks to handle large files efficiently.
    
    Args:
        file_path: Path to the file to read
        chunk_size: Size of each chunk in bytes
        
    Yields:
        Lists of complete lines from the file
    """
    incomplete_line = ''
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
                
            # Process the chunk into lines
            lines = (incomplete_line + chunk).split('\n')
            
            # If the chunk doesn't end with a newline, the last line is incomplete
            if chunk.endswith('\n'):
                incomplete_line = ''
            else:
                incomplete_line = lines.pop()
                
            yield lines
    
    # Don't forget the last incomplete line if there is one
    if incomplete_line:
        yield [incomplete_line]


def detect_encoding(file_path: str) -> str:
    """
    Attempt to detect the encoding of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected encoding or 'utf-8' as fallback
    """
    # Expanded list of encodings to try, in order of preference
    encodings = [
        'utf-8', 'latin-1', 'utf-16', 'utf-16-le', 'utf-16-be', 
        'ascii', 'cp1252', 'iso-8859-1', 'iso-8859-2', 'iso-8859-15',
        'windows-1250', 'windows-1251', 'windows-1252', 'windows-1253',
        'windows-1254', 'windows-1255', 'windows-1256', 'windows-1257',
        'big5', 'gb2312', 'euc-jp', 'shift-jis', 'euc-kr', 'utf-32',
        'utf-32-le', 'utf-32-be'
    ]
    
    # First, try to use chardet if available for more accurate detection
    try:
        import chardet
        with open(file_path, 'rb') as file:
            sample = file.read(4096)  # Read larger sample for better detection
            if sample:
                result = chardet.detect(sample)
                if result['confidence'] > 0.7:  # Only accept high confidence detections
                    logging.info(f"Detected encoding with chardet: {result['encoding']} ({result['confidence']:.2f} confidence)")
                    return result['encoding']
    except ImportError:
        logging.debug("chardet module not available, falling back to manual detection")
    except Exception as e:
        logging.debug(f"Error using chardet: {str(e)}")
    
    # Fallback to manual detection
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                file.read(1024)  # Read a small sample
                return encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logging.debug(f"Error checking encoding {encoding}: {str(e)}")
    
    # If all else fails, use UTF-8 with fallback
    logging.warning(f"Could not confidently detect encoding for {file_path}, using UTF-8 as fallback")
    return 'utf-8'  # Default fallback


class Spinner:
    """A simple progress spinner for small operations."""
    
    def __init__(self, message="Processing", delay=0.1):
        """Initialize the spinner with a message and delay."""
        self.message = message
        self.delay = delay
        self.spinner_cycle = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.running = False
        self.spinner_thread = None
        
    def __enter__(self):
        """Start the spinner when entering a context."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the spinner when exiting a context."""
        self.stop()
        
    def start(self):
        """Start the spinner in a separate thread."""
        self.running = True
        self.spinner_thread = threading.Thread(target=self._spin)
        self.spinner_thread.daemon = True
        self.spinner_thread.start()
        
    def stop(self):
        """Stop the spinner."""
        self.running = False
        if self.spinner_thread:
            self.spinner_thread.join()
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()
        
    def _spin(self):
        """Display the spinner animation."""
        while self.running:
            frame = next(self.spinner_cycle)
            sys.stdout.write(f'\r{frame} {self.message}... ')
            sys.stdout.flush()
            time.sleep(self.delay)


def remove_duplicates(file_path: str, comparison_mode: str = "case-insensitive", 
                      create_backup: bool = False, show_progress: bool = True,
                      output_file: Optional[str] = None, chunk_size: int = 1024*1024,
                      dry_run: bool = False, similarity_threshold: float = 0.8,
                      backup_extension: str = ".bak", preserve_permissions: bool = False,
                      exclude_pattern: Optional[str] = None) -> Dict:
    """
    Remove duplicate lines from a text file based on specified comparison mode.
    
    Args:
        file_path: Path to the text file to process
        comparison_mode: How to compare lines 
        create_backup: Whether to create a backup of the original file
        show_progress: Whether to show a progress bar
        output_file: Optional path to write results (instead of overwriting input)
        chunk_size: Size of chunks when processing large files
        dry_run: If True, only report what would be done without making changes
        similarity_threshold: Threshold for fuzzy matching (0-1)
        backup_extension: Extension for backup files
        preserve_permissions: Whether to preserve file permissions when writing output files
        exclude_pattern: Regex pattern for lines to exclude from processing
    
    Returns:
        Dictionary containing statistics about the operation
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read or written
        ValueError: If invalid parameters are provided
    """
    # Input validation
    if not file_path:
        raise ValueError("File path cannot be empty")
        
    if comparison_mode not in ["case-insensitive", "case-sensitive", "whitespace-insensitive", 
                              "content-hash", "alphanumeric-only", "fuzzy"]:
        raise ValueError(f"Invalid comparison mode: {comparison_mode}")
        
    if similarity_threshold < 0 or similarity_threshold > 1:
        raise ValueError(f"Similarity threshold must be between 0 and 1, got: {similarity_threshold}")
        
    if chunk_size <= 0:
        raise ValueError(f"Chunk size must be positive, got: {chunk_size}")
        
    # If output file is specified, validate it
    if output_file:
        try:
            # Check if the directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logging.info(f"Created output directory: {output_dir}")
                
            # Check if we can write to the output file
            with open(output_file, 'a', encoding='utf-8') as f:
                pass
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cannot write to output file {output_file}: {str(e)}")
    
    try:
        # Check if file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Check if file is readable
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.read(1)
        except PermissionError as e:
            raise PermissionError(f"Permission denied: Cannot read file {file_path}: {str(e)}")
        except OSError as e:
            raise OSError(f"Operating system error when reading {file_path}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Cannot read file {file_path}: {str(e)}")
        
        # Get file size for progress tracking
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logging.warning(f"File {file_path} is empty")
                
                # Return early for empty files
                stats = {
                    "total_lines": 0,
                    "unique_lines": 0,
                    "duplicates_removed": 0,
                    "file_path": file_path,
                    "dry_run": dry_run
                }
                return stats
        except OSError as e:
            logging.warning(f"Could not get file size for {file_path}: {str(e)}")
            file_size = 0
        
        # Create backup if requested
        if create_backup and not dry_run:
            backup_path = f"{file_path}{backup_extension}"
            logging.info(f"Creating backup at: {backup_path}")
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logging.warning(f"Failed to create backup at {backup_path}: {str(e)}")
                if not dry_run:
                    raise  # Only raise if not in dry run mode
        
        # Detect encoding
        encoding = detect_encoding(file_path)
        logging.info(f"Detected encoding: {encoding}")
        
        # Initialize tracking variables
        total_lines = 0
        unique_lines = []
        seen_lines = set()
        
        # Setup progress bar or spinner based on file size
        pbar = None
        spinner = None
        if show_progress:
            if file_size > chunk_size:
                pbar = tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Processing {os.path.basename(file_path)}")
            else:
                spinner = Spinner(f"Processing {os.path.basename(file_path)}")
                spinner.start()
        
        # Process file in chunks for memory efficiency
        try:
            for chunk in chunk_reader(file_path, chunk_size):
                if pbar:
                    pbar.update(len('\n'.join(chunk).encode(encoding, errors='ignore')))
                
                # Process this chunk of lines
                chunk_lines, chunk_seen = process_lines(chunk, comparison_mode, show_progress, similarity_threshold, exclude_pattern)
                
                total_lines += len(chunk)
                unique_lines.extend(chunk_lines)
                seen_lines.update(chunk_seen)
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}")
            if pbar:
                pbar.close()
            if spinner:
                spinner.stop()
            raise
        
        # Close progress tracking
        if pbar:
            pbar.close()
        if spinner:
            spinner.stop()
        
        # Calculate statistics
        unique_count = len(unique_lines)
        duplicates_removed = total_lines - unique_count
        
        # In dry run mode, just return stats without writing
        if dry_run:
            logging.info(f"Dry run: would remove {duplicates_removed} duplicates from {file_path}")
        else:
            # Determine where to write the results
            target_file = output_file if output_file else file_path
            
            # Get original file permissions if needed
            original_mode = None
            if preserve_permissions:
                try:
                    original_mode = os.stat(file_path).st_mode
                    logging.debug(f"Preserving file permissions: {original_mode}")
                except Exception as e:
                    logging.warning(f"Could not get file permissions for {file_path}: {str(e)}")
            
            # Write the unique lines
            logging.info(f"Writing {unique_count} unique lines to {target_file}")
            try:
                with open(target_file, 'w', encoding=encoding, errors='ignore') as file:
                    file.writelines(unique_lines)
                
                # Restore original permissions if needed
                if preserve_permissions and original_mode is not None:
                    try:
                        os.chmod(target_file, original_mode)
                        logging.debug(f"Restored permissions for {target_file}")
                    except Exception as e:
                        logging.warning(f"Could not restore permissions for {target_file}: {str(e)}")
                    
            except Exception as e:
                logging.error(f"Error writing to {target_file}: {str(e)}")
                raise
        
        # Return statistics
        stats = {
            "total_lines": total_lines,
            "unique_lines": unique_count,
            "duplicates_removed": duplicates_removed,
            "file_path": file_path,
            "dry_run": dry_run
        }
        
        return stats
        
    except PermissionError:
        logging.error(f"Permission denied: Unable to read or write to {file_path}")
        raise
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise


def normalize_line(
    line: str, 
    mode: str = "case-sensitive",
    language: Optional[str] = None,
    auto_detect: bool = False,
    detect_per_line: bool = False
) -> str:
    """
    Normalize a line of text based on the specified comparison mode.
    
    Args:
        line: The line to normalize
        mode: Comparison mode (case-sensitive, case-insensitive, etc.)
        language: Optional language code for language-specific processing
        auto_detect: Whether to automatically detect the language
        detect_per_line: Whether to detect language for each line
        
    Returns:
        Normalized line for comparison
    """
    # Handle empty lines
    if not line or line.isspace():
        return ""
        
    # Apply normalization based on mode
    if mode == "case-insensitive":
        # Convert to lowercase for case-insensitive comparison
        return line.lower()
        
    elif mode == "whitespace-insensitive":
        # Remove all whitespace for whitespace-insensitive comparison
        return re.sub(r'\s+', '', line)
        
    elif mode == "content-hash":
        # Generate a hash of the line content
        import hashlib
        return hashlib.md5(line.encode('utf-8')).hexdigest()
        
    elif mode == "alphanumeric-only":
        # Keep only alphanumeric characters
        return ''.join(c for c in line if c.isalnum())
        
    elif mode == "fuzzy":
        # For fuzzy mode, we still need to normalize the line
        # Actual fuzzy comparison happens during matching
        return line.lower().strip()
        
    # Default to case-sensitive (no normalization)
    return line


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate a similarity score between two strings using Jaccard similarity.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0 and 1
    """
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    
    if not set1 and not set2:
        return 1.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0


def is_fuzzy_duplicate(normalized: str, seen_lines: Set[str], threshold: float) -> bool:
    """
    Check if a line is a fuzzy duplicate of any seen line.
    
    Args:
        normalized: Normalized version of the current line
        seen_lines: Set of previously seen normalized lines
        threshold: Similarity threshold (0-1)
        
    Returns:
        True if the line is a fuzzy duplicate, False otherwise
    """
    if not normalized or threshold >= 1.0:
        return False
        
    # Quick rejection: if there are no words in common, it can't be a duplicate
    # This speeds up processing significantly for large datasets
    normalized_words = set(normalized.lower().split())
    if not normalized_words:  # Empty line
        return False
        
    # For very large seen_lines sets, use a more optimized approach
    if len(seen_lines) > 10000:
        # Create an index of common words for faster filtering
        # This is a simplified version of an inverted index
        word_to_lines = {}
        
        # Sample the seen lines to build a smaller index
        sample_size = min(1000, len(seen_lines))
        import random
        sample = random.sample(list(seen_lines), sample_size) if len(seen_lines) > sample_size else seen_lines
        
        # Build word index from the sample
        for line in sample:
            words = set(line.lower().split())
            for word in words:
                if len(word) > 3:  # Only index longer words for efficiency
                    if word not in word_to_lines:
                        word_to_lines[word] = []
                    word_to_lines[word].append(line)
        
        # Find candidates that share words with the normalized line
        candidates = set()
        for word in normalized_words:
            if len(word) > 3 and word in word_to_lines:
                candidates.update(word_to_lines[word])
        
        # Now check similarity only with candidates
        for candidate in candidates:
            if calculate_similarity(normalized, candidate) >= threshold:
                return True
        
        # If no candidates or no matches, try a small random sample
        if len(sample) > 100:
            small_sample = random.sample(sample, 50)
            for seen in small_sample:
                if calculate_similarity(normalized, seen) >= threshold:
                    return True
    # For small to medium sets, use the previous approach
    elif len(seen_lines) < 1000:
        for seen in seen_lines:
            if calculate_similarity(normalized, seen) >= threshold:
                return True
    else:
        # For medium-sized sets, use random sampling
        import random
        sample_size = min(100, len(seen_lines))
        sample = random.sample(list(seen_lines), sample_size)
        for seen in sample:
            if calculate_similarity(normalized, seen) >= threshold:
                return True
    
    return False


def process_lines(lines: List[str], comparison_mode: str, show_progress: bool, 
                  similarity_threshold: float = 1.0, exclude_pattern: Optional[str] = None) -> Tuple[List[str], Set[str]]:
    """
    Process the lines from the file to remove duplicates while preserving order.
    
    Args:
        lines: List of lines from the file
        comparison_mode: How to compare lines
        show_progress: Whether to show a progress bar
        similarity_threshold: Threshold for fuzzy matching (0-1)
        exclude_pattern: Regex pattern for lines to exclude from processing
    
    Returns:
        A tuple containing (list of unique lines, set of normalized lines seen)
    """
    # Use a generator expression to avoid loading all lines into memory if possible
    unique_lines = []
    
    # Using a set for exact matches and a list for fuzzy matches to optimize memory usage
    seen_exact = set()
    
    # Compile regex pattern if provided
    exclude_regex = None
    if exclude_pattern:
        try:
            exclude_regex = re.compile(exclude_pattern)
            logging.debug(f"Using exclude pattern: {exclude_pattern}")
        except re.error as e:
            logging.error(f"Invalid regex pattern: {exclude_pattern} - {str(e)}")
            logging.warning("Continuing without exclude pattern")
    
    # For very large files with fuzzy matching, we'll use a bloom filter-like approach
    # to reduce memory usage at the cost of a small chance of false positives
    using_fuzzy = comparison_mode == "fuzzy" and similarity_threshold < 1.0
    fuzzy_matches = []
    
    # Sampling rate for fuzzy matching to improve performance on very large files
    fuzzy_sample_rate = 0.3 if len(lines) > 100000 else 1.0
    
    # Create iterator with progress bar if requested
    if show_progress and len(lines) > 1000:
        line_iterator = tqdm(lines, desc="Processing lines", unit="lines", leave=False)
    else:
        line_iterator = lines
    
    # Process each line
    for line in line_iterator:
        # Add newline if it's missing (for chunks)
        if not line.endswith('\n') and line:
            line = line + '\n'
            
        # Skip processing for empty lines
        if not line.strip():
            # Only add empty line if we haven't seen it before (preserve some formatting)
            if not any(l.strip() == '' for l in unique_lines[-3:] if unique_lines):
                unique_lines.append(line)
            continue
        
        # Skip lines matching the exclude pattern
        if exclude_regex and exclude_regex.search(line):
            logging.debug(f"Skipping excluded line: {line.strip()}")
            unique_lines.append(line)  # Keep the line but don't check for duplicates
            continue
            
        # Normalize the line for comparison based on comparison mode
        normalized = normalize_line(line, "case-insensitive" if using_fuzzy else comparison_mode)
        
        # Skip if empty after normalization
        if normalized == "":
            continue
            
        # Check if we've seen this line before (exact match)
        if normalized in seen_exact:
            continue
            
        # For fuzzy mode, check similarity if not an exact duplicate
        is_duplicate = False
        if using_fuzzy:
            # Use random sampling for very large files to improve performance
            import random
            if random.random() <= fuzzy_sample_rate:
                is_duplicate = is_fuzzy_duplicate(normalized, set(fuzzy_matches), similarity_threshold)
                
                # Only add to fuzzy matches if it's not a duplicate (to keep the set smaller)
                if not is_duplicate:
                    # Keep the fuzzy matches list from growing too large
                    if len(fuzzy_matches) > 10000:
                        # Remove random elements to keep size manageable
                        del fuzzy_matches[:1000]
                    fuzzy_matches.append(normalized)
        
        if not is_duplicate:
            # This is a new unique line
            seen_exact.add(normalized)
            unique_lines.append(line)
    
    # For return compatibility
    return unique_lines, seen_exact


def find_text_files(directory: str, recursive: bool = False, pattern: str = "*.txt") -> List[str]:
    """
    Find all text files in a directory.
    
    Args:
        directory: Directory to search in
        recursive: Whether to search recursively
        pattern: Glob pattern for files to match
        
    Returns:
        List of paths to text files
    """
    search_path = Path(directory)
    glob_pattern = f"**/{pattern}" if recursive else pattern
    
    return [str(path) for path in search_path.glob(glob_pattern) if path.is_file()]


def process_multiple_files(file_paths: List[str], comparison_mode: str,
                         create_backup: bool, show_progress: bool,
                         output_dir: Optional[str] = None, 
                         parallel: bool = False, max_workers: int = None,
                         chunk_size: int = 1024*1024,
                         dry_run: bool = False,
                         similarity_threshold: float = 0.8,
                         backup_extension: str = ".bak",
                         preserve_permissions: bool = False,
                         exclude_pattern: Optional[str] = None) -> List[Dict]:
    """
    Process multiple files and remove duplicates from each.
    
    Args:
        file_paths: List of paths to process
        comparison_mode: Comparison mode to use
        create_backup: Whether to create backups
        show_progress: Whether to show progress bars
        output_dir: Optional directory to write results to (instead of overwriting)
        parallel: Whether to process files in parallel
        max_workers: Maximum number of parallel workers
        chunk_size: Size of chunks when processing large files
        dry_run: If True, only report what would be done without making changes
        similarity_threshold: Threshold for fuzzy matching (0-1)
        backup_extension: Extension for backup files
        preserve_permissions: Whether to preserve file permissions when writing output files
        exclude_pattern: Regex pattern for lines to exclude from processing
        
    Returns:
        List of statistics dictionaries for each file
    """
    results = []
    
    if not file_paths:
        logging.warning("No files found to process")
        return results
    
    # Determine output files if output_dir is specified
    output_files = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_files = {path: os.path.join(output_dir, os.path.basename(path)) for path in file_paths}
    
    for file_path in file_paths:
        try:
            result = remove_duplicates(
                file_path, comparison_mode, create_backup, show_progress,
                output_files[file_path] if output_files else None, 1024*1024, dry_run, similarity_threshold, 
                backup_extension, preserve_permissions, exclude_pattern
            )
            
            results.append(result)
            
            # Log the results for this file
            logging.info(f"Results for {file_path}:")
            logging.info(f"  Original line count: {result['total_lines']}")
            logging.info(f"  Unique lines: {result['unique_lines']}")
            logging.info(f"  Duplicates removed: {result['duplicates_removed']}")
            
        except Exception as e:
            logging.error(f"Failed to process {file_path}: {str(e)}")
            results.append({"file_path": file_path, "error": str(e)})
    
    return results


def generate_report(
    report_data: Dict, 
    output_file: Optional[str] = None,
    report_type: str = "text"
) -> None:
    """
    Generate a report of the duplicate removal process.
    
    Args:
        report_data: Dictionary containing report information
        output_file: Optional path to save the report
        report_type: Type of report to generate (text, json, csv)
        
    Returns:
        None
    """
    if not output_file:
        # Return if no output file is specified
        logger.debug("No output file specified for report, skipping")
        return
        
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Generate report based on specified type
        if report_type.lower() == "json":
            # JSON format
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
                
        elif report_type.lower() == "csv":
            # CSV format
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    "Timestamp", "File", "Total Lines", "Unique Lines", 
                    "Duplicates Removed", "Duplicate Rate (%)"
                ])
                
                # Write data for each file
                timestamp = report_data.get("timestamp", datetime.now().isoformat())
                for file_info in report_data.get("results", {}).get("files", []):
                    total = file_info.get("total_lines", 0)
                    unique = file_info.get("unique_lines", 0)
                    duplicates = file_info.get("duplicates_removed", 0)
                    
                    # Calculate duplicate rate
                    dup_rate = 0
                    if total > 0:
                        dup_rate = (duplicates / total) * 100
                        
                    writer.writerow([
                        timestamp,
                        file_info.get("file_path", "Unknown"),
                        total,
                        unique,
                        duplicates,
                        f"{dup_rate:.2f}"
                    ])
                    
        else:
            # Default text format
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"DupeRemover Report\n")
                f.write(f"=================\n\n")
                f.write(f"Generated: {report_data.get('timestamp', datetime.now().isoformat())}\n\n")
                
                # Summary information
                results = report_data.get("results", {})
                f.write(f"Summary:\n")
                f.write(f"  Files Processed: {results.get('files_processed', 0)}\n")
                f.write(f"  Failed Files: {results.get('failed_files', 0)}\n")
                f.write(f"  Total Lines: {results.get('total_lines', 0)}\n")
                f.write(f"  Unique Lines: {results.get('unique_lines', 0)}\n\n")
                
                # Details for each file
                f.write(f"File Details:\n")
                for file_info in results.get("files", []):
                    f.write(f"  - {file_info.get('file_path', 'Unknown')}:\n")
                    f.write(f"    Total Lines: {file_info.get('total_lines', 0)}\n")
                    f.write(f"    Unique Lines: {file_info.get('unique_lines', 0)}\n")
                    f.write(f"    Duplicates Removed: {file_info.get('duplicates_removed', 0)}\n")
                    
                    # Calculate duplicate rate
                    total = file_info.get("total_lines", 0)
                    duplicates = file_info.get("duplicates_removed", 0)
                    if total > 0:
                        dup_rate = (duplicates / total) * 100
                        f.write(f"    Duplicate Rate: {dup_rate:.2f}%\n")
                    f.write("\n")
                
        logger.info(f"Report saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to generate report: {str(e)}")
        
    return


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Remove duplicate lines from text files with various options."
    )
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_source = input_group.add_mutually_exclusive_group()
    input_source.add_argument(
        "files", 
        nargs="*", 
        help="One or more text files to process",
        default=[]
    )
    input_source.add_argument(
        "-d", "--directory",
        help="Process all text files in the specified directory"
    )
    input_group.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively process directories (only with --directory)"
    )
    input_group.add_argument(
        "--pattern",
        default="*.txt",
        help="File pattern to match when using --directory (default: *.txt)"
    )
    
    # Comparison options
    comparison_group = parser.add_argument_group('Comparison Options')
    comparison_group.add_argument(
        "-m", "--mode",
        choices=["case-insensitive", "case-sensitive", "whitespace-insensitive", 
                "content-hash", "alphanumeric-only", "fuzzy"],
        default="case-insensitive",
        help="Comparison mode for identifying duplicates (default: case-insensitive)"
    )
    comparison_group.add_argument(
        "--similarity",
        type=float,
        default=0.8,
        help="Similarity threshold for fuzzy matching (0-1, default: 0.8, only with --mode fuzzy)"
    )
    comparison_group.add_argument(
        "--exclude-pattern",
        help="Regex pattern for lines to exclude from processing"
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        "-o", "--output-dir",
        help="Directory to write processed files to (instead of overwriting)"
    )
    output_group.add_argument(
        "--report",
        choices=["text", "json", "html", "csv", "xml", "yaml", "markdown"],
        default="text",
        help="Format for the results report (default: text)"
    )
    output_group.add_argument(
        "--report-file",
        help="File to write the report to (default: print to console)"
    )
    
    # Processing options
    process_group = parser.add_argument_group('Processing Options')
    process_group.add_argument(
        "-b", "--backup",
        action="store_true",
        help="Create backup files before making changes"
    )
    process_group.add_argument(
        "--backup-ext",
        default=".bak",
        help="Extension for backup files (default: .bak)"
    )
    process_group.add_argument(
        "--preserve-permissions",
        action="store_true",
        help="Preserve file permissions when writing output files"
    )
    process_group.add_argument(
        "-p", "--progress",
        action="store_true",
        help="Show progress bar when processing"
    )
    process_group.add_argument(
        "--parallel",
        action="store_true",
        help="Process multiple files in parallel"
    )
    process_group.add_argument(
        "--workers",
        type=int,
        help="Maximum number of parallel workers (default: number of CPU cores)"
    )
    process_group.add_argument(
        "--chunk-size",
        type=int,
        default=1024*1024,  # 1MB
        help="Chunk size in bytes for processing large files (default: 1MB)"
    )
    
    # Streaming mode options
    streaming_group = parser.add_argument_group('Streaming Mode Options')
    streaming_group.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming mode to process data as it arrives"
    )
    streaming_group.add_argument(
        "--follow",
        action="store_true",
        help="Continue watching the file for changes (like 'tail -f')"
    )
    streaming_group.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Seconds between file checks in streaming mode (default: 0.5s)"
    )
    streaming_group.add_argument(
        "--buffer-size",
        type=int,
        default=10000,
        help="Maximum number of recent lines to keep in buffer (default: 10000)"
    )
    streaming_group.add_argument(
        "--max-runtime",
        type=float,
        help="Maximum runtime in seconds for streaming mode"
    )
    
    # Other options
    other_group = parser.add_argument_group('Other Options')
    other_group.add_argument(
        "--log-file",
        help="File to write logs to"
    )
    other_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    other_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    other_group.add_argument(
        "--color",
        action="store_true",
        help="Enable colored output in text reports"
    )
    
    other_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all non-error output"
    )
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Check for version flag first
    if args.version:
        print(f"DupeRemover version {__version__}")
        sys.exit(0)
    
    # Configure logging based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled")
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    
    # Check for required files
    if not args.files and not args.stdin:
        logger.error("No input files specified and --stdin not used")
        sys.exit(1)
    
    # Handle streaming mode if enabled
    if args.stream:
        if len(args.files) != 1 and not args.stdin:
            logger.error("Streaming mode requires exactly one input file or stdin")
            sys.exit(1)
        
        input_file = args.files[0] if args.files else "-"
        if input_file == "-":
            logger.error("Streaming from stdin not implemented yet")
            sys.exit(1)
            
        logger.info(f"Starting streaming mode for {input_file}")
        stream_stats = stream_process_file(
            file_path=input_file,
            mode=args.mode,
            follow=args.follow,
            language=args.language,
            auto_detect_language=args.auto_detect_language,
            detect_per_line=args.detect_per_line,
            exclude_pattern=args.exclude_pattern,
            poll_interval=args.poll_interval,
            buffer_size=args.buffer_size,
            max_runtime=args.max_runtime
        )
        
        # Generate report if requested
        if args.report:
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "command_args": vars(args),
                "results": {
                    "files_processed": 1,
                    "failed_files": 0,
                    "total_lines": stream_stats["total_lines"],
                    "unique_lines": stream_stats["unique_lines"],
                    "files": [stream_stats]
                }
            }
            
            generate_report(report_data, args.report, args.report_file, args.color)
        
        sys.exit(0)
    
    # ... existing code for normal processing ...


def stream_process_file(
    file_path: str,
    mode: str = "case-sensitive",
    follow: bool = False,
    language: Optional[str] = None,
    auto_detect_language: bool = False,
    detect_per_line: bool = False,
    exclude_pattern: Optional[str] = None,
    poll_interval: float = 0.5,
    buffer_size: int = 10000,
    max_runtime: Optional[float] = None
) -> Dict:
    """
    Process a file in streaming mode, handling new content as it is added.
    
    Args:
        file_path: Path to the file to process
        mode: Comparison mode for determining duplicates
        follow: Continue watching the file for changes
        language: Language code for language-specific processing
        auto_detect_language: Whether to auto-detect the language
        detect_per_line: Whether to detect language for each line
        exclude_pattern: Regex pattern for lines to exclude
        poll_interval: Seconds between file checks in follow mode
        buffer_size: Maximum number of recent lines to keep in buffer
        max_runtime: Maximum runtime in seconds
        
    Returns:
        Statistics about the processed file
    """
    # Setup signal handling for graceful exit
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        logger.info(f"Received signal {sig}, shutting down...")
        running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize statistics
    stats = {
        "file_path": file_path,
        "total_lines": 0,
        "unique_lines": 0,
        "duplicates_removed": 0,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "runtime_seconds": 0
    }
    
    # Prepare exclude pattern if provided
    exclude_regex = None
    if exclude_pattern:
        try:
            exclude_regex = re.compile(exclude_pattern)
        except re.error as e:
            logger.error(f"Invalid exclude pattern: {str(e)}")
            return stats
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File '{file_path}' does not exist")
        return stats
        
    # Initialize line tracking
    seen_lines = set()
    recent_lines = []  # For ringbuffer implementation
    file_size = os.path.getsize(file_path)
    last_position = 0
    start_time = time.time()
    
    logger.info(f"Starting streaming mode for file: {file_path}")
    logger.info(f"Mode: {mode}, Follow: {follow}")
    
    try:
        while running:
            current_size = os.path.getsize(file_path)
            
            # Check if file was truncated
            if current_size < last_position:
                logger.warning("File was truncated, resetting position")
                last_position = 0
                
            # If file has new content
            if current_size > last_position:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    last_position = f.tell()
                
                if new_content:
                    new_lines = new_content.splitlines()
                    
                    for line in new_lines:
                        # Update statistics
                        stats["total_lines"] += 1
                        
                        # Check if line matches exclude pattern
                        if exclude_regex and exclude_regex.search(line):
                            continue
                            
                        # Process line based on mode and language settings
                        processed_line = normalize_line(
                            line, 
                            mode=mode,
                            language=language,
                            auto_detect=auto_detect_language,
                            detect_per_line=detect_per_line
                        )
                        
                        # Skip if it's a duplicate
                        if processed_line in seen_lines:
                            stats["duplicates_removed"] += 1
                            continue
                            
                        # Add to seen lines
                        seen_lines.add(processed_line)
                        stats["unique_lines"] += 1
                        
                        # Add to recent lines buffer (ring buffer)
                        recent_lines.append(line)
                        if len(recent_lines) > buffer_size:
                            oldest_line = recent_lines.pop(0)
                            
                        # Print unique line to stdout
                        print(line)
                        
            # Check if we should continue running
            if not follow:
                break
                
            # Check if max runtime has been reached
            if max_runtime and (time.time() - start_time) > max_runtime:
                logger.info(f"Maximum runtime of {max_runtime}s reached")
                break
                
            # Sleep before checking again
            time.sleep(poll_interval)
    except Exception as e:
        logger.error(f"Error in streaming mode: {str(e)}")
    finally:
        # Update final statistics
        end_time = time.time()
        stats["end_time"] = datetime.now().isoformat()
        stats["runtime_seconds"] = end_time - start_time
        
    logger.info(f"Streaming mode completed: {stats['total_lines']} lines processed, "
                f"{stats['unique_lines']} unique, {stats['duplicates_removed']} duplicates removed")
    
    return stats


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation canceled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unhandled error: {str(e)}")
        sys.exit(1)