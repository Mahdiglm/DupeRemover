# DupeRemover v2.0.4 Release Notes

## Release Date: July 25, 2025

This release introduces an important new feature that allows users to exclude specific lines from deduplication processing, along with several performance improvements and bug fixes.

## New Features

### Pattern Exclusion

- **New `--exclude-pattern` command-line option**: Specify a regex pattern to preserve matching lines
  ```
  python main.py your_file.txt --exclude-pattern "^IMPORTANT:"
  ```
- All lines matching the specified pattern will be preserved in the output file regardless of duplication
- Ideal for keeping header lines, timestamps, section markers, or other important content
- Full regex syntax support with proper validation and error handling

### Streaming Mode Improvements

- Added pattern exclusion support to streaming mode
- Optimized buffer management for more efficient real-time processing
- Reduced memory footprint when watching large log files

## Performance Enhancements

- Optimized regex pattern compilation and caching
- Improved memory efficiency when processing large files with exclude patterns
- Skip unnecessary pattern matching for empty lines and whitespace-only content
- More efficient handling of special cases in streaming mode

## Bug Fixes

- Fixed indentation issues in try-except blocks
- Corrected memory leak when processing extremely large files with certain pattern combinations
- Improved error handling and reporting for malformed regex patterns
- Fixed edge case where empty lines weren't properly processed with exclusion patterns
- Resolved issues with streaming mode buffer management

## Documentation

- Added comprehensive examples for pattern exclusion in README
- Updated command-line help text with detailed pattern usage examples
- Included warnings and guidelines for complex regex patterns
- Enhanced troubleshooting section with pattern-related tips

## Upgrade Notes

This version is fully backward compatible with previous 2.x versions. No changes to existing workflows are required unless you want to take advantage of the new pattern exclusion feature.

## Examples

### Exclude lines beginning with specific text

```bash
python main.py logs.txt --exclude-pattern "^[0-9]{4}-[0-9]{2}-[0-9]{2}"
```

### Exclude lines containing specific words

```bash
python main.py data.txt --exclude-pattern "WARNING|ERROR|CRITICAL"
```

### Exclude lines with specific formatting

```bash
python main.py config.txt --exclude-pattern "^#.*$"
```

## Known Issues

- Complex regex patterns may impact performance on very large files
- Pattern matching is performed before fuzzy matching in fuzzy mode
- UTF-16 encoded files may require special handling with certain patterns
