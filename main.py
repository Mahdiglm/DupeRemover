"""
duplicate_remover.py - Removes duplicates from text files with various comparison options.
Supports multiple files, progress tracking, and backup creation.
Version 2.0.0 - Enhanced with parallel processing, directory support, and more advanced features.
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
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
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
    encodings = ['utf-8', 'latin-1', 'utf-16', 'ascii']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                file.read(1024)  # Read a small sample
                return encoding
        except UnicodeDecodeError:
            continue
    
    return 'utf-8'  # Default fallback


def remove_duplicates(file_path: str, comparison_mode: str = "case-insensitive", 
                      create_backup: bool = False, show_progress: bool = True,
                      output_file: Optional[str] = None, chunk_size: int = 1024*1024,
                      dry_run: bool = False, similarity_threshold: float = 0.8) -> Dict:
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
    
    Returns:
        Dictionary containing statistics about the operation
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read or written
    """
    try:
        # Check if file exists
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file size for progress tracking
        file_size = os.path.getsize(file_path)
        
        # Create backup if requested
        if create_backup and not dry_run:
            backup_path = f"{file_path}.bak"
            logging.info(f"Creating backup at: {backup_path}")
            shutil.copy2(file_path, backup_path)
        
        # Detect encoding
        encoding = detect_encoding(file_path)
        logging.info(f"Detected encoding: {encoding}")
        
        # Initialize tracking variables
        total_lines = 0
        unique_lines = []
        seen_lines = set()
        
        # Setup progress bar if requested
        pbar = None
        if show_progress and file_size > chunk_size:
            pbar = tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Processing {os.path.basename(file_path)}")
        
        # Process file in chunks for memory efficiency
        for chunk in chunk_reader(file_path, chunk_size):
            if pbar:
                pbar.update(len('\n'.join(chunk).encode(encoding)))
            
            # Process this chunk of lines
            chunk_lines, chunk_seen = process_lines(chunk, comparison_mode, show_progress, similarity_threshold)
            
            total_lines += len(chunk)
            unique_lines.extend(chunk_lines)
            seen_lines.update(chunk_seen)
        
        # Close progress bar if it was created
        if pbar:
            pbar.close()
        
        # Calculate statistics
        unique_count = len(unique_lines)
        duplicates_removed = total_lines - unique_count
        
        # In dry run mode, just return stats without writing
        if dry_run:
            logging.info(f"Dry run: would remove {duplicates_removed} duplicates from {file_path}")
        else:
            # Determine where to write the results
            target_file = output_file if output_file else file_path
            
            # Write the unique lines
            logging.info(f"Writing {unique_count} unique lines to {target_file}")
            with open(target_file, 'w', encoding=encoding) as file:
                file.writelines(unique_lines)
        
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


def normalize_line(line: str, comparison_mode: str) -> str:
    """
    Normalize a line based on the comparison mode.
    
    Args:
        line: The line to normalize
        comparison_mode: The comparison mode to use
        
    Returns:
        Normalized line string
    """
    if comparison_mode == "case-insensitive":
        return line.strip().lower()
    elif comparison_mode == "case-sensitive":
        return line.strip()
    elif comparison_mode == "whitespace-insensitive":
        return ''.join(line.split()).lower()
    elif comparison_mode == "content-hash":
        # Creates a hash of sorted words to identify semantically similar content regardless of order
        words = sorted(word.lower() for word in re.findall(r'\w+', line))
        return hashlib.md5(' '.join(words).encode()).hexdigest()
    elif comparison_mode == "alphanumeric-only":
        # Only consider alphanumeric characters
        return ''.join(c.lower() for c in line if c.isalnum())
    else:
        return line.strip().lower()  # Default to case-insensitive


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
        
    # For small sets of seen lines, check each one
    if len(seen_lines) < 1000:
        for seen in seen_lines:
            if calculate_similarity(normalized, seen) >= threshold:
                return True
    else:
        # For larger sets, only check against a sample to maintain performance
        sample_size = min(100, len(seen_lines))
        sample = list(itertools.islice(seen_lines, sample_size))
        for seen in sample:
            if calculate_similarity(normalized, seen) >= threshold:
                return True
    
    return False


def process_lines(lines: List[str], comparison_mode: str, show_progress: bool, 
                  similarity_threshold: float = 1.0) -> Tuple[List[str], Set[str]]:
    """
    Process the lines from the file to remove duplicates while preserving order.
    
    Args:
        lines: List of lines from the file
        comparison_mode: How to compare lines
        show_progress: Whether to show a progress bar
        similarity_threshold: Threshold for fuzzy matching (0-1)
    
    Returns:
        A tuple containing (list of unique lines, set of normalized lines seen)
    """
    unique_lines = []
    seen_lines = set()
    
    # Create iterator with progress bar if requested
    if show_progress and len(lines) > 1000:
        line_iterator = tqdm(lines, desc="Processing lines", unit="lines", leave=False)
    else:
        line_iterator = lines
    
    # Special handling for fuzzy matching
    using_fuzzy = comparison_mode == "fuzzy" and similarity_threshold < 1.0
    
    for line in line_iterator:
        # Add newline if it's missing (for chunks)
        if not line.endswith('\n') and line:
            line = line + '\n'
            
        # Normalize the line for comparison based on comparison mode
        normalized = normalize_line(line, "case-insensitive" if using_fuzzy else comparison_mode)
        
        # Check if we've seen this line before
        is_duplicate = normalized in seen_lines
        
        # For fuzzy mode, also check similarity if not an exact duplicate
        if using_fuzzy and not is_duplicate:
            is_duplicate = is_fuzzy_duplicate(normalized, seen_lines, similarity_threshold)
        
        if not is_duplicate and normalized != "":
            # This is a new unique line
            seen_lines.add(normalized)
            unique_lines.append(line)
        elif normalized == "" and line not in unique_lines:
            # Special handling for empty lines (preserve line breaks/formatting)
            unique_lines.append(line)
    
    return unique_lines, seen_lines


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
                         similarity_threshold: float = 0.8) -> List[Dict]:
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
    
    if parallel and len(file_paths) > 1:
        logging.info(f"Processing {len(file_paths)} files in parallel")
        
        # Define a function for parallel execution
        def process_file(file_path):
            try:
                output_file = output_files[file_path] if output_files else None
                return remove_duplicates(file_path, comparison_mode, create_backup, 
                                        show_progress, output_file, chunk_size,
                                        dry_run, similarity_threshold)
            except Exception as e:
                logging.error(f"Failed to process {file_path}: {str(e)}")
                return {"file_path": file_path, "error": str(e)}
        
        # Process files in parallel
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_file, path): path for path in file_paths}
            
            if show_progress:
                futures_iterator = tqdm(concurrent.futures.as_completed(futures), 
                                       total=len(file_paths), desc="Files", unit="file")
            else:
                futures_iterator = concurrent.futures.as_completed(futures)
            
            for future in futures_iterator:
                file_path = futures[future]
                try:
                    stats = future.result()
                    results.append(stats)
                    
                    if "error" not in stats:
                        logging.info(f"Results for {file_path}:")
                        logging.info(f"  Original line count: {stats['total_lines']}")
                        logging.info(f"  Unique lines: {stats['unique_lines']}")
                        logging.info(f"  Duplicates removed: {stats['duplicates_removed']}")
                except Exception as e:
                    logging.error(f"Exception processing {file_path}: {str(e)}")
                    results.append({"file_path": file_path, "error": str(e)})
    else:
        # Process files sequentially
        for file_path in file_paths:
            try:
                output_file = output_files[file_path] if output_files else None
                stats = remove_duplicates(file_path, comparison_mode, create_backup, 
                                         show_progress, output_file, chunk_size,
                                         dry_run, similarity_threshold)
                results.append(stats)
                
                # Log the results for this file
                logging.info(f"Results for {file_path}:")
                logging.info(f"  Original line count: {stats['total_lines']}")
                logging.info(f"  Unique lines: {stats['unique_lines']}")
                logging.info(f"  Duplicates removed: {stats['duplicates_removed']}")
                
            except Exception as e:
                logging.error(f"Failed to process {file_path}: {str(e)}")
                results.append({"file_path": file_path, "error": str(e)})
    
    return results


def generate_report(results: List[Dict], output_format: str = "text", 
                   report_file: Optional[str] = None) -> str:
    """
    Generate a report of the results.
    
    Args:
        results: List of result dictionaries
        output_format: Format for the report ('text', 'json', or 'html')
        report_file: Optional path to write the report to
        
    Returns:
        The report as a string
    """
    import json
    from datetime import datetime
    
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    total_processed = len(successful)
    total_failed = len(failed)
    total_lines = sum(r.get('total_lines', 0) for r in successful)
    total_unique = sum(r.get('unique_lines', 0) for r in successful)
    total_removed = sum(r.get('duplicates_removed', 0) for r in successful)
    
    if output_format == "json":
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "files_processed": total_processed,
                "files_failed": total_failed,
                "total_lines": total_lines,
                "unique_lines": total_unique,
                "duplicates_removed": total_removed,
                "duplication_rate": (total_removed / total_lines) if total_lines > 0 else 0
            },
            "results": results
        }
        output = json.dumps(report, indent=2)
        
    elif output_format == "html":
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <title>DupeRemover Results</title>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; margin: 20px; }",
            "    .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }",
            "    table { border-collapse: collapse; width: 100%; margin-top: 20px; }",
            "    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "    th { background-color: #f2f2f2; }",
            "    tr:nth-child(even) { background-color: #f9f9f9; }",
            "    .error { color: red; }",
            "  </style>",
            "</head>",
            "<body>",
            f"  <h1>DupeRemover Results</h1>",
            f"  <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            "  <div class='summary'>",
            f"    <h2>Summary</h2>",
            f"    <p>Files processed: {total_processed}</p>",
            f"    <p>Files failed: {total_failed}</p>",
            f"    <p>Total lines: {total_lines}</p>",
            f"    <p>Unique lines: {total_unique}</p>",
            f"    <p>Duplicates removed: {total_removed}</p>",
            f"    <p>Duplication rate: {(total_removed / total_lines * 100):.2f}% (if applicable)</p>",
            "  </div>",
            "  <h2>File Details</h2>",
            "  <table>",
            "    <tr><th>File</th><th>Total Lines</th><th>Unique Lines</th><th>Duplicates Removed</th><th>Status</th></tr>"
        ]
        
        for r in results:
            if "error" in r:
                html.append(f"    <tr><td>{r['file_path']}</td><td>-</td><td>-</td><td>-</td><td class='error'>{r['error']}</td></tr>")
            else:
                html.append(f"    <tr><td>{r['file_path']}</td><td>{r['total_lines']}</td><td>{r['unique_lines']}</td>" +
                           f"<td>{r['duplicates_removed']}</td><td>{'Dry run' if r.get('dry_run', False) else 'Success'}</td></tr>")
        
        html.extend([
            "  </table>",
            "</body>",
            "</html>"
        ])
        
        output = "\n".join(html)
    
    else:  # text format
        lines = [
            "=== DupeRemover Results ===",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY:",
            f"Files processed: {total_processed}/{len(results)}",
            f"Files failed: {total_failed}",
            f"Total lines processed: {total_lines}",
            f"Total unique lines: {total_unique}",
            f"Total duplicates removed: {total_removed}",
            f"Overall duplication rate: {(total_removed / total_lines * 100):.2f}% (if applicable)",
            "",
            "DETAILS:"
        ]
        
        for r in results:
            if "error" in r:
                lines.append(f"[ERROR] {r['file_path']}: {r['error']}")
            else:
                dry_run_prefix = "[DRY RUN] " if r.get('dry_run', False) else ""
                lines.append(f"{dry_run_prefix}{r['file_path']}:")
                lines.append(f"  - Total lines: {r['total_lines']}")
                lines.append(f"  - Unique lines: {r['unique_lines']}")
                lines.append(f"  - Duplicates removed: {r['duplicates_removed']}")
                lines.append(f"  - Duplication rate: {(r['duplicates_removed'] / r['total_lines'] * 100):.2f}%")
        
        output = "\n".join(lines)
    
    # Write to file if specified
    if report_file:
        try:
            with open(report_file, 'w', encoding='utf-8') as file:
                file.write(output)
            logging.info(f"Report written to {report_file}")
        except Exception as e:
            logging.error(f"Failed to write report: {str(e)}")
    
    return output


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
        help="One or more text files to process"
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
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        "-o", "--output-dir",
        help="Directory to write processed files to (instead of overwriting)"
    )
    output_group.add_argument(
        "--report",
        choices=["text", "json", "html"],
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
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose, args.log_file)
    
    # Ensure at least one input source is provided
    if not args.files and not args.directory:
        logging.error("Error: No input files or directory specified")
        print("Please provide either file paths or a directory with the -d option")
        print("Run 'python main.py --help' for usage information")
        sys.exit(1)
    
    # Collect all files to process
    file_paths = []
    
    if args.directory:
        logging.info(f"Searching for {args.pattern} files in {args.directory}")
        file_paths = find_text_files(args.directory, args.recursive, args.pattern)
        logging.info(f"Found {len(file_paths)} files to process")
    else:
        file_paths = args.files
    
    if not file_paths:
        logging.error("No files found to process")
        sys.exit(1)
    
    # Process files
    logging.info(f"Starting duplicate removal on {len(file_paths)} file(s)")
    start_time = os.times()
    
    results = process_multiple_files(
        file_paths, 
        args.mode, 
        args.backup, 
        args.progress,
        args.output_dir,
        args.parallel,
        args.workers,
        args.chunk_size,
        args.dry_run,
        args.similarity if args.mode == "fuzzy" else 1.0
    )
    
    end_time = os.times()
    elapsed = end_time.user - start_time.user + end_time.system - start_time.system
    
    # Generate and display report
    report = generate_report(results, args.report, args.report_file)
    if not args.report_file:
        print("\n" + report)
    
    # Print timing information
    print(f"\nProcessing completed in {elapsed:.2f} seconds")
    
    logging.info("Duplicate removal completed")
    
    # Exit with error code if any files failed
    if any("error" in r for r in results):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation canceled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unhandled error: {str(e)}")
        sys.exit(1)