"""
duplicate_remover.py - Removes duplicates from text files with various comparison options.
Supports multiple files, progress tracking, and backup creation.
"""

import os
import sys
import logging
import argparse
import shutil
from typing import List, Set, Dict, Tuple
from tqdm import tqdm


def setup_logging(verbose: bool = False) -> None:
    """Configure the logging system."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def remove_duplicates(file_path: str, comparison_mode: str = "case-insensitive", 
                      create_backup: bool = False, show_progress: bool = True) -> Dict:
    """
    Remove duplicate lines from a text file based on specified comparison mode.
    
    Args:
        file_path: Path to the text file to process
        comparison_mode: How to compare lines ("case-insensitive", "case-sensitive", "whitespace-insensitive")
        create_backup: Whether to create a backup of the original file
        show_progress: Whether to show a progress bar
    
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
        
        # Create backup if requested
        if create_backup:
            backup_path = f"{file_path}.bak"
            logging.info(f"Creating backup at: {backup_path}")
            shutil.copy2(file_path, backup_path)
        
        # Read the file contents
        logging.info(f"Reading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            lines = file.readlines()
        
        # Process lines and remove duplicates
        unique_lines, seen_lines = process_lines(lines, comparison_mode, show_progress)
        
        # Calculate statistics
        total_lines = len(lines)
        unique_count = len(unique_lines)
        duplicates_removed = total_lines - unique_count
        
        # Write the unique lines back to the file
        logging.info(f"Writing {unique_count} unique lines back to file")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(unique_lines)
        
        # Return statistics
        stats = {
            "total_lines": total_lines,
            "unique_lines": unique_count,
            "duplicates_removed": duplicates_removed,
            "file_path": file_path
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
    elif comparison_mode == "whitespace-insensitive":
        return ''.join(line.split()).lower()
    elif comparison_mode == "case-sensitive":
        return line.strip()
    else:
        return line.strip().lower()  # Default to case-insensitive


def process_lines(lines: List[str], comparison_mode: str, show_progress: bool) -> Tuple[List[str], Set[str]]:
    """
    Process the lines from the file to remove duplicates while preserving order.
    
    Args:
        lines: List of lines from the file
        comparison_mode: How to compare lines
        show_progress: Whether to show a progress bar
    
    Returns:
        A tuple containing (list of unique lines, set of normalized lines seen)
    """
    unique_lines = []
    seen_lines = set()
    
    # Create iterator with progress bar if requested
    if show_progress and len(lines) > 1000:
        line_iterator = tqdm(lines, desc="Processing lines", unit="lines")
    else:
        line_iterator = lines
    
    for line in line_iterator:
        # Normalize the line for comparison based on comparison mode
        normalized = normalize_line(line, comparison_mode)
        
        # Check if we've seen this line before
        if normalized not in seen_lines and normalized != "":
            # This is a new unique line
            seen_lines.add(normalized)
            unique_lines.append(line)
        elif normalized == "" and line not in unique_lines:
            # Special handling for empty lines (preserve line breaks/formatting)
            unique_lines.append(line)
    
    return unique_lines, seen_lines


def process_multiple_files(file_paths: List[str], comparison_mode: str,
                         create_backup: bool, show_progress: bool) -> List[Dict]:
    """
    Process multiple files and remove duplicates from each.
    
    Args:
        file_paths: List of paths to process
        comparison_mode: Comparison mode to use
        create_backup: Whether to create backups
        show_progress: Whether to show progress bars
        
    Returns:
        List of statistics dictionaries for each file
    """
    results = []
    
    for file_path in file_paths:
        try:
            stats = remove_duplicates(file_path, comparison_mode, create_backup, show_progress)
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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Remove duplicate lines from text files with various options."
    )
    
    parser.add_argument(
        "files", 
        nargs="+", 
        help="One or more text files to process"
    )
    
    parser.add_argument(
        "-m", "--mode",
        choices=["case-insensitive", "case-sensitive", "whitespace-insensitive"],
        default="case-insensitive",
        help="Comparison mode for identifying duplicates (default: case-insensitive)"
    )
    
    parser.add_argument(
        "-b", "--backup",
        action="store_true",
        help="Create backup files before making changes"
    )
    
    parser.add_argument(
        "-p", "--progress",
        action="store_true",
        help="Show progress bar when processing large files"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Process files
    logging.info(f"Starting duplicate removal on {len(args.files)} file(s)")
    results = process_multiple_files(
        args.files, 
        args.mode, 
        args.backup, 
        args.progress
    )
    
    # Print summary
    total_removed = sum(r.get('duplicates_removed', 0) for r in results if 'duplicates_removed' in r)
    successful = sum(1 for r in results if 'error' not in r)
    failed = len(results) - successful
    
    print("\nSUMMARY:")
    print(f"Files processed: {successful}/{len(args.files)}")
    if failed > 0:
        print(f"Files failed: {failed}")
    print(f"Total duplicates removed: {total_removed}")
    print(f"Comparison mode: {args.mode}")
    
    logging.info("Duplicate removal completed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation canceled by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unhandled error: {str(e)}")
        sys.exit(1)