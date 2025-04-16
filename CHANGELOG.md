# Changelog

All notable changes to DupeRemover will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note:** Version 2.0.0 is the final planned major release. The project is now in maintenance mode, accepting only bug fixes and minor improvements.

## [2.1.0] - Unreleased

### Added

- TBD

## [2.0.4] - 2025-07-25

### Added

- **Pattern Exclusion**: New `--exclude-pattern` command-line option allows users to specify a regex pattern for lines that should be excluded from deduplication processing
  - Lines matching the pattern are preserved in the output regardless of duplication
  - Especially useful for preserving headers, timestamps, or other special content
  - Supports all standard regex syntax with proper error handling for invalid patterns
- **Streaming Mode Enhancements**:
  - Improved buffer management for real-time processing
  - Added pattern exclusion support to streaming mode
  - Better memory usage when following large log files
- **Performance Improvements**:
  - Optimized regex pattern compilation and matching
  - More efficient handling of very large files with exclude patterns
  - Reduced unnecessary pattern matching for empty lines
- **Documentation**:
  - Added comprehensive examples for pattern exclusion in README
  - Updated help documentation with detailed pattern usage examples
  - Added warnings and guidelines for complex regex patterns

### Fixed

- Indentation issues in try-except blocks
- Memory leak when processing extremely large files with certain pattern combinations
- Improved error handling for malformed regex patterns
- Fixed edge case where empty lines weren't properly processed with exclusion patterns

## [2.0.3] - 2025-07-15

### Added

- Command-line option for colored output in text reports (`--color`)
- Progress spinner for small file operations
- Quiet mode to suppress non-error output (`-q/--quiet`)
- Option to customize backup file extension (`--backup-ext`)

## [2.0.2] - 2025-07-01

### Added

- New report format options:
  - CSV format for spreadsheet compatibility
  - XML format for structured data processing
  - YAML format for configuration-style output
  - Markdown format for documentation-friendly reports
- Expanded encoding detection with support for additional international character sets
- Improved error handling with more specific error messages

## [2.0.1] - 2025-06-18

### Fixed

- Improved handling of encoding errors by using 'ignore' mode consistently throughout the codebase
- Fixed issues with files that have mixed or non-standard encodings
- Enhanced error reporting for file read/write operations

## [2.0.0] - 2025-06-15

### Added

- Parallel processing for multiple files with configurable worker count
- Memory-efficient chunk processing for handling extremely large files
- Directory processing with recursive option
- New comparison modes:
  - "content-hash" - ignores word order in lines
  - "alphanumeric-only" - ignores all non-alphanumeric characters
  - "fuzzy" - finds near-duplicate lines based on similarity threshold
- Smart file encoding detection
- Output options:
  - Save processed files to a different directory
  - Generate reports in multiple formats (text, JSON, HTML)
- Dry run mode to preview changes without modifying files
- Optional log file creation
- Enhanced progress tracking with file size estimation
- Performance metrics and timing information

### Changed

- Completely overhauled command-line interface with argument groups
- Improved error handling and reporting
- Enhanced logging system with configurable handlers
- Progress bar improvements

### Fixed

- Handling of incomplete lines in chunked file reading
- More robust handling of various file encodings
- Performance optimizations for fuzzy matching with large files

## [1.0.0] - 2025-04-10

### Added

- Initial release of DupeRemover
- Multiple comparison modes (case-insensitive, case-sensitive, whitespace-insensitive)
- Command-line interface with help documentation
- Progress bar for large file processing
- Backup file creation option
- Multiple file processing support
- Detailed logging with verbose option
- Comprehensive error handling
- Documentation and usage examples
