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

- New `--exclude-pattern` command-line option for excluding lines matching a regex pattern from deduplication
- Improved handling of special cases in streaming mode
- Enhanced documentation with examples for pattern exclusion
- Better error reporting for invalid regex patterns

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
