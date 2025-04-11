# Changelog

All notable changes to DupeRemover will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
