"""
duplicate_remover.py - Removes duplicates from text files with various comparison options.
Supports multiple files, progress tracking, and backup creation.
Version 2.0.4-dev - Development version for future enhancements.
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
    Attempt to detect the encoding of a file with enhanced language support.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected encoding or 'utf-8' as fallback
    """
    # Dictionary of common encodings by language/region
    language_encodings = {
        # Western languages
        'western': ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'iso-8859-15'],
        # Eastern European
        'eastern_european': ['iso-8859-2', 'cp1250', 'windows-1250', 'iso-8859-3'],
        # Cyrillic (Russian, Bulgarian, etc.)
        'cyrillic': ['cp1251', 'windows-1251', 'iso-8859-5', 'koi8-r', 'koi8-u'],
        # Greek
        'greek': ['iso-8859-7', 'cp1253', 'windows-1253'],
        # Turkish
        'turkish': ['iso-8859-9', 'cp1254', 'windows-1254'],
        # Hebrew
        'hebrew': ['iso-8859-8', 'cp1255', 'windows-1255'],
        # Arabic
        'arabic': ['iso-8859-6', 'cp1256', 'windows-1256'],
        # Baltic
        'baltic': ['iso-8859-4', 'cp1257', 'windows-1257'],
        # East Asian (Chinese, Japanese, Korean)
        'east_asian': ['gb2312', 'gbk', 'gb18030', 'big5', 'shift-jis', 'euc-jp', 'iso-2022-jp', 'euc-kr'],
        # Unicode
        'unicode': ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le', 'utf-32-be']
    }
    
    # Flatten the dictionary to a prioritized list
    # Start with unicode, then western, then add all others
    encodings = language_encodings['unicode'] + language_encodings['western']
    for lang, encs in language_encodings.items():
        if lang not in ['unicode', 'western']:
            encodings.extend(encs)
    
    # Remove duplicates while preserving order
    unique_encodings = []
    for enc in encodings:
        if enc not in unique_encodings:
            unique_encodings.append(enc)
    
    # Try to use chardet for more accurate detection
    try:
        import chardet
        with open(file_path, 'rb') as file:
            # Read larger sample for better detection (up to 1MB)
            sample = file.read(1024 * 1024)
            if sample:
                result = chardet.detect(sample)
                confidence_threshold = 0.7
                if result['confidence'] > confidence_threshold:
                    logging.info(f"Detected encoding with chardet: {result['encoding']} ({result['confidence']:.2f} confidence)")
                    return result['encoding']
                logging.debug(f"Chardet detection too low confidence: {result}")
    except ImportError:
        logging.debug("chardet module not available, falling back to manual detection")
    except Exception as e:
        logging.debug(f"Error using chardet: {str(e)}")
    
    # Enhanced byte signature detection
    try:
        with open(file_path, 'rb') as file:
            raw = file.read(4)
            # BOM detection
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            elif raw.startswith(b'\xfe\xff'):
                return 'utf-16-be'
            elif raw.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            elif raw.startswith(b'\x00\x00\xfe\xff'):
                return 'utf-32-be'
            elif raw.startswith(b'\xff\xfe\x00\x00'):
                return 'utf-32-le'
    except Exception as e:
        logging.debug(f"Error in BOM detection: {str(e)}")
    
    # Sample-based heuristic detection
    try:
        with open(file_path, 'rb') as file:
            sample = file.read(4096)
            
            # Try to detect UTF-8 by checking for valid UTF-8 sequences
            try:
                sample.decode('utf-8')
                # If it decodes as UTF-8 without errors, it's very likely UTF-8
                return 'utf-8'
            except UnicodeDecodeError:
                pass
            
            # Check for high frequency of NULL bytes which suggests UTF-16/UTF-32
            null_count = sample.count(b'\x00')
            if null_count > len(sample) * 0.3:
                # Try different UTF-16/UTF-32 variants
                for enc in ['utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le', 'utf-32-be']:
                    try:
                        sample.decode(enc)
                        return enc
                    except UnicodeDecodeError:
                        continue
            
            # Check for specific language markers
            # East Asian detection (high bytes common)
            high_byte_count = sum(1 for b in sample if b > 127)
            if high_byte_count > len(sample) * 0.3:
                # Try East Asian encodings first
                for enc in language_encodings['east_asian']:
                    try:
                        with open(file_path, 'r', encoding=enc, errors='strict') as f:
                            f.read(100)
                        return enc
                    except UnicodeDecodeError:
                        continue
    except Exception as e:
        logging.debug(f"Error in heuristic detection: {str(e)}")
    
    # Fallback to trying encodings one by one
    for encoding in unique_encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='strict') as file:
                file.read(1024)  # Read a small sample with strict error checking
                logging.info(f"Successfully detected encoding: {encoding}")
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
                      exclude_pattern: Optional[str] = None, language: Optional[str] = None,
                      auto_detect_language: bool = False, detect_per_line: bool = False) -> Dict:
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
        language: Specific language code for normalization
        auto_detect_language: Whether to automatically detect the document language
        detect_per_line: Whether to detect language per line (for mixed content)
    
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
                chunk_lines, chunk_seen = process_lines(
                    chunk, comparison_mode, show_progress, similarity_threshold, 
                    exclude_pattern, language, 
                    auto_detect_language or detect_per_line
                )
                
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


def normalize_line(line: str, comparison_mode: str, language: str = None) -> str:
    """
    Normalize a line based on the comparison mode and language.
    
    Args:
        line: The line to normalize
        comparison_mode: The comparison mode to use
        language: Language-specific normalization (auto-detect if None)
        
    Returns:
        Normalized line string
    """
    # First try to detect the language if not specified
    if language is None:
        try:
            # Try to use langdetect for automatic language detection
            import langdetect
            # Only attempt detection on lines with enough content
            if len(line.strip()) > 20:
                try:
                    detected = langdetect.detect(line)
                    language = detected
                    logging.debug(f"Detected language: {language}")
                except langdetect.lang_detect_exception.LangDetectException:
                    # If detection fails, default to None
                    logging.debug("Language detection failed, using generic normalization")
            else:
                logging.debug("Line too short for language detection")
        except ImportError:
            logging.debug("langdetect module not available, using generic normalization")
    
    # Apply language-specific normalization
    if language:
        # Unicode normalization (handles combining characters)
        import unicodedata
        line = unicodedata.normalize('NFKC', line)
        
        # Language-specific handling
        if language in ['zh', 'zh-cn', 'zh-tw']:  # Chinese
            try:
                # Try to handle traditional vs simplified Chinese
                # This requires the 'hanziconv' library
                from hanziconv import HanziConv
                if comparison_mode == "case-insensitive":
                    # Convert to simplified for comparison
                    return HanziConv.toSimplified(line.strip())
                else:
                    return line.strip()
            except ImportError:
                logging.debug("hanziconv not available for Chinese normalization")
                return line.strip()
        
        elif language in ['ja']:  # Japanese
            # For Japanese, handle full-width/half-width characters
            try:
                import mojimoji
                # Convert all full-width chars to half-width where possible
                normalized = mojimoji.zen_to_han(line, kana=False)
                if comparison_mode == "case-insensitive":
                    return normalized.strip().lower()
                else:
                    return normalized.strip()
            except ImportError:
                logging.debug("mojimoji not available for Japanese normalization")
                if comparison_mode == "case-insensitive":
                    return line.strip().lower()
                else:
                    return line.strip()
        
        elif language in ['ko']:  # Korean
            # For Korean, handle Hangul normalization
            try:
                from hangul_utils import normalize_hangul
                normalized = normalize_hangul(line)
                if comparison_mode == "case-insensitive":
                    return normalized.strip().lower()
                else:
                    return normalized.strip()
            except ImportError:
                logging.debug("hangul_utils not available for Korean normalization")
                if comparison_mode == "case-insensitive":
                    return line.strip().lower()
                else:
                    return line.strip()
        
        elif language in ['ar', 'fa', 'ur']:  # Arabic, Persian, Urdu
            # Handle Arabic/Persian normalization (remove diacritics, normalize letter forms)
            try:
                # Try to use pyarabic for Arabic text normalization
                from pyarabic.araby import normalize_hamza, normalize_teh, normalize_alef
                from pyarabic.araby import strip_tashkeel, strip_tatweel
                
                normalized = line
                normalized = strip_tashkeel(normalized)  # Remove diacritics
                normalized = strip_tatweel(normalized)   # Remove tatweel (stretching character)
                normalized = normalize_hamza(normalized) # Normalize hamza forms
                normalized = normalize_alef(normalized)  # Normalize alef forms
                normalized = normalize_teh(normalized)   # Normalize teh forms
                
                return normalized.strip()
            except ImportError:
                logging.debug("pyarabic not available for Arabic text normalization")
                if comparison_mode == "case-insensitive":
                    return line.strip().lower()
                else:
                    return line.strip()
    
    # Fall back to standard normalization if no language-specific handling
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
                  similarity_threshold: float = 1.0, exclude_pattern: Optional[str] = None,
                  language: Optional[str] = None, auto_detect_language: bool = False) -> Tuple[List[str], Set[str]]:
    """
    Process the lines from the file to remove duplicates while preserving order.
    
    Args:
        lines: List of lines from the file
        comparison_mode: How to compare lines
        show_progress: Whether to show a progress bar
        similarity_threshold: Threshold for fuzzy matching (0-1)
        exclude_pattern: Regex pattern for lines to exclude from processing
        language: Specific language code for normalization (None for auto)
        auto_detect_language: Whether to attempt language detection for each line
    
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
    
    # Try to detect the dominant language in the file if auto_detect_language is True
    dominant_language = None
    if auto_detect_language and language is None:
        try:
            import langdetect
            # Sample up to 50 lines for language detection
            sample_text = " ".join([line for line in lines[:50] if len(line.strip()) > 5])
            if len(sample_text) > 100:  # Only detect if we have enough text
                try:
                    # Try to get language with probability distribution
                    langs = langdetect.detect_langs(sample_text)
                    if langs and langs[0].prob > 0.5:  # Use the most probable language if confidence is high
                        dominant_language = langs[0].lang
                        logging.info(f"Detected dominant language: {dominant_language} (confidence: {langs[0].prob:.2f})")
                except:
                    # Fall back to simpler detection
                    try:
                        dominant_language = langdetect.detect(sample_text)
                        logging.info(f"Detected dominant language: {dominant_language}")
                    except:
                        logging.debug("Failed to detect dominant language")
        except ImportError:
            logging.debug("langdetect module not available for language detection")
    
    # Use the specified language if provided, otherwise use the detected dominant language
    working_language = language if language is not None else dominant_language
    
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
        
        # Detect language for this specific line if auto_detect_language is True
        line_language = None
        if auto_detect_language and working_language is None and len(line.strip()) > 20:
            try:
                import langdetect
                try:
                    line_language = langdetect.detect(line)
                    logging.debug(f"Line language detected: {line_language}")
                except langdetect.lang_detect_exception.LangDetectException:
                    pass
            except ImportError:
                pass
            
        # Use line-specific language if detected, otherwise use the working language
        current_language = line_language if line_language else working_language
            
        # Normalize the line for comparison based on comparison mode and language
        normalized = normalize_line(line, "case-insensitive" if using_fuzzy else comparison_mode, 
                                   language=current_language)
        
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
                         exclude_pattern: Optional[str] = None,
                         language: Optional[str] = None,
                         auto_detect_language: bool = False,
                         detect_per_line: bool = False) -> List[Dict]:
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
        language: Specific language code for normalization
        auto_detect_language: Whether to automatically detect the document language
        detect_per_line: Whether to detect language per line (for mixed content)
        
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
    
    # Define a function for file processing (used in both parallel and sequential modes)
    def process_file(file_path):
        try:
            output_file = output_files[file_path] if output_files else None
            return remove_duplicates(file_path, comparison_mode, create_backup, 
                                    show_progress, output_file, chunk_size,
                                    dry_run, similarity_threshold, backup_extension,
                                    preserve_permissions, exclude_pattern,
                                    language, auto_detect_language, detect_per_line)
        except Exception as e:
            logging.error(f"Failed to process {file_path}: {str(e)}")
            return {"file_path": file_path, "error": str(e)}
    
    if parallel and len(file_paths) > 1:
        logging.info(f"Processing {len(file_paths)} files in parallel")
        
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
                stats = process_file(file_path)
                results.append(stats)
                
                # Log the results for this file
                if "error" not in stats:
                    logging.info(f"Results for {file_path}:")
                    logging.info(f"  Original line count: {stats['total_lines']}")
                    logging.info(f"  Unique lines: {stats['unique_lines']}")
                    logging.info(f"  Duplicates removed: {stats['duplicates_removed']}")
                
            except Exception as e:
                logging.error(f"Failed to process {file_path}: {str(e)}")
                results.append({"file_path": file_path, "error": str(e)})
    
    return results


def generate_report(results: List[Dict], output_format: str = "text", 
                   report_file: Optional[str] = None, use_color: bool = False) -> str:
    """
    Generate a report of the results.
    
    Args:
        results: List of result dictionaries
        output_format: Format for the report ('text', 'json', 'html', 'csv', 'xml', 'yaml', or 'markdown')
        report_file: Optional path to write the report to
        use_color: Whether to use colors in text output (only applies to text format)
        
    Returns:
        The report as a string
    """
    import json
    from datetime import datetime
    import csv
    import io
    import xml.dom.minidom as md
    from xml.etree import ElementTree as ET
    
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    total_processed = len(successful)
    total_failed = len(failed)
    total_lines = sum(r.get('total_lines', 0) for r in successful)
    total_unique = sum(r.get('unique_lines', 0) for r in successful)
    total_removed = sum(r.get('duplicates_removed', 0) for r in successful)
    
    if output_format == "markdown":
        lines = [
            "# DupeRemover Results",
            f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Summary",
            "",
            f"- **Files processed:** {total_processed}/{len(results)}",
            f"- **Files failed:** {total_failed}",
            f"- **Total lines processed:** {total_lines}",
            f"- **Total unique lines:** {total_unique}",
            f"- **Total duplicates removed:** {total_removed}",
            f"- **Overall duplication rate:** {(total_removed / total_lines * 100):.2f}% (if applicable)" if total_lines > 0 else "- **Overall duplication rate:** 0.00% (if applicable)",
            "",
            "## Details",
            "",
            "| File | Total Lines | Unique Lines | Duplicates Removed | Duplication Rate | Status |",
            "|------|-------------|--------------|-------------------|-----------------|--------|"
        ]
        
        for r in results:
            if "error" in r:
                lines.append(f"| {r['file_path']} | - | - | - | - | ❌ **ERROR:** {r['error']} |")
            else:
                duplication_rate = f"{(r['duplicates_removed'] / r['total_lines'] * 100):.2f}%" if r['total_lines'] > 0 else "0.00%"
                status = "⚠️ **DRY RUN**" if r.get('dry_run', False) else "✅ **Success**"
                lines.append(f"| {r['file_path']} | {r['total_lines']} | {r['unique_lines']} | {r['duplicates_removed']} | {duplication_rate} | {status} |")
        
        output = "\n".join(lines)
    
    elif output_format == "yaml":
        try:
            import yaml
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
            output = yaml.dump(report, sort_keys=False, default_flow_style=False)
        except ImportError:
            logging.warning("PyYAML library not installed. Falling back to text format.")
            # Recursively call with text format
            return generate_report(results, "text", report_file, use_color)
    
    elif output_format == "json":
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
    
    elif output_format == "csv":
        # Use StringIO to build the CSV data as a string
        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output)
        
        # Write the header row with timestamp
        csv_writer.writerow(['DupeRemover Results', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        csv_writer.writerow([])  # Empty row for separation
        
        # Write the summary section
        csv_writer.writerow(['SUMMARY'])
        csv_writer.writerow(['Files processed', f'{total_processed}/{len(results)}'])
        csv_writer.writerow(['Files failed', total_failed])
        csv_writer.writerow(['Total lines processed', total_lines])
        csv_writer.writerow(['Total unique lines', total_unique])
        csv_writer.writerow(['Total duplicates removed', total_removed])
        csv_writer.writerow(['Overall duplication rate', f'{(total_removed / total_lines * 100):.2f}%' if total_lines > 0 else '0.00%'])
        csv_writer.writerow([])  # Empty row for separation
        
        # Write the details section header
        csv_writer.writerow(['DETAILS'])
        csv_writer.writerow(['File', 'Total Lines', 'Unique Lines', 'Duplicates Removed', 'Duplication Rate', 'Status'])
        
        # Write the details for each file
        for r in results:
            if "error" in r:
                csv_writer.writerow([r['file_path'], '-', '-', '-', '-', f'ERROR: {r["error"]}'])
            else:
                duplication_rate = f"{(r['duplicates_removed'] / r['total_lines'] * 100):.2f}%" if r['total_lines'] > 0 else "0.00%"
                status = 'Dry run' if r.get('dry_run', False) else 'Success'
                csv_writer.writerow([
                    r['file_path'],
                    r['total_lines'],
                    r['unique_lines'],
                    r['duplicates_removed'],
                    duplication_rate,
                    status
                ])
        
        output = csv_output.getvalue()
    
    elif output_format == "xml":
        # Create XML structure
        root = ET.Element("DupeRemover")
        root.set("timestamp", datetime.now().isoformat())
        
        # Add summary section
        summary = ET.SubElement(root, "Summary")
        ET.SubElement(summary, "FilesProcessed").text = str(total_processed)
        ET.SubElement(summary, "FilesFailed").text = str(total_failed)
        ET.SubElement(summary, "TotalLines").text = str(total_lines)
        ET.SubElement(summary, "UniqueLines").text = str(total_unique)
        ET.SubElement(summary, "DuplicatesRemoved").text = str(total_removed)
        
        duplication_rate = (total_removed / total_lines * 100) if total_lines > 0 else 0
        ET.SubElement(summary, "DuplicationRate").text = f"{duplication_rate:.2f}%"
        
        # Add details section
        details = ET.SubElement(root, "Details")
        
        # Add file results
        for r in results:
            file_elem = ET.SubElement(details, "File")
            ET.SubElement(file_elem, "Path").text = r["file_path"]
            
            if "error" in r:
                ET.SubElement(file_elem, "Status").text = "Error"
                ET.SubElement(file_elem, "Error").text = r["error"]
            else:
                ET.SubElement(file_elem, "Status").text = "Dry run" if r.get("dry_run", False) else "Success"
                ET.SubElement(file_elem, "TotalLines").text = str(r["total_lines"])
                ET.SubElement(file_elem, "UniqueLines").text = str(r["unique_lines"])
                ET.SubElement(file_elem, "DuplicatesRemoved").text = str(r["duplicates_removed"])
                
                duplication_rate = (r["duplicates_removed"] / r["total_lines"] * 100) if r["total_lines"] > 0 else 0
                ET.SubElement(file_elem, "DuplicationRate").text = f"{duplication_rate:.2f}%"
        
        # Convert to pretty-printed XML
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = md.parseString(rough_string)
        output = reparsed.toprettyxml(indent="  ")
    
    else:  # text format
        # Define ANSI color codes if color is enabled
        if use_color:
            HEADER = '\033[95m'
            BLUE = '\033[94m'
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            RED = '\033[91m'
            ENDC = '\033[0m'
            BOLD = '\033[1m'
        else:
            HEADER = BLUE = GREEN = YELLOW = RED = ENDC = BOLD = ''
            
        lines = [
            f"{HEADER}=== DupeRemover Results ==={ENDC}",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"{BOLD}SUMMARY:{ENDC}",
            f"Files processed: {GREEN}{total_processed}/{len(results)}{ENDC}",
            f"Files failed: {RED if total_failed > 0 else GREEN}{total_failed}{ENDC}",
            f"Total lines processed: {BLUE}{total_lines}{ENDC}",
            f"Total unique lines: {BLUE}{total_unique}{ENDC}",
            f"Total duplicates removed: {YELLOW}{total_removed}{ENDC}",
            f"Overall duplication rate: {YELLOW}{(total_removed / total_lines * 100):.2f}%{ENDC} (if applicable)" if total_lines > 0 else f"Overall duplication rate: {YELLOW}0.00%{ENDC} (if applicable)",
            "",
            f"{BOLD}DETAILS:{ENDC}"
        ]
        
        for r in results:
            if "error" in r:
                lines.append(f"{RED}[ERROR] {r['file_path']}: {r['error']}{ENDC}")
            else:
                dry_run_prefix = f"{BLUE}[DRY RUN]{ENDC} " if r.get('dry_run', False) else ""
                lines.append(f"{dry_run_prefix}{BOLD}{r['file_path']}:{ENDC}")
                lines.append(f"  - Total lines: {r['total_lines']}")
                lines.append(f"  - Unique lines: {r['unique_lines']}")
                lines.append(f"  - Duplicates removed: {YELLOW}{r['duplicates_removed']}{ENDC}")
                duplication_rate = (r['duplicates_removed'] / r['total_lines'] * 100) if r['total_lines'] > 0 else 0
                lines.append(f"  - Duplication rate: {YELLOW}{duplication_rate:.2f}%{ENDC}")
        
        output = "\n".join(lines)
    
    # Write to file if specified
    if report_file:
        try:
            with open(report_file, 'w', encoding='utf-8', errors='ignore') as file:
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
    
    # Language options
    language_group = parser.add_argument_group('Language Options')
    language_group.add_argument(
        "--language",
        help="Specify language code for better text normalization (e.g., en, zh, ja, ko, ar)"
    )
    language_group.add_argument(
        "--auto-detect-language",
        action="store_true",
        help="Automatically detect language for normalization"
    )
    language_group.add_argument(
        "--detect-per-line",
        action="store_true",
        help="Detect language for each line individually (slower but more accurate for mixed language files)"
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


def main() -> None:
    """Main entry point for the script."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    if args.quiet:
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')
        if args.log_file:
            # Add file handler for all logs despite quiet mode
            file_handler = logging.FileHandler(args.log_file, mode='w')
            file_handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(file_handler)
    else:
        setup_logging(args.verbose, args.log_file)
    
    # Ensure at least one input source is provided
    if not args.files and not args.directory:
        logging.error("Error: No input files or directory specified")
        print("Please provide either file paths or a directory with the -d option")
        print("Run 'python main.py --help' for usage information")
        sys.exit(1)
    
    # Validate language options
    if args.detect_per_line and not args.auto_detect_language:
        logging.warning("--detect-per-line requires --auto-detect-language. Enabling auto detection.")
        args.auto_detect_language = True
    
    # Check for required language modules and warn if not available
    if args.auto_detect_language or args.language:
        try:
            import langdetect
            logging.info("Language detection enabled using langdetect module")
        except ImportError:
            logging.warning("langdetect module not found. Install with 'pip install langdetect' for language detection")
            if args.auto_detect_language:
                logging.warning("Auto language detection disabled due to missing dependency")
                args.auto_detect_language = False
                args.detect_per_line = False
    
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
        args.similarity if args.mode == "fuzzy" else 1.0,
        args.backup_ext,
        args.preserve_permissions,
        args.exclude_pattern,
        args.language,
        args.auto_detect_language,
        args.detect_per_line
    )
    
    end_time = os.times()
    elapsed = end_time.user - start_time.user + end_time.system - start_time.system
    
    # Generate and display report
    report = generate_report(results, args.report, args.report_file, args.color)
    if not args.report_file and not args.quiet:
        print("\n" + report)
    
    # Print timing information
    if not args.quiet:
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