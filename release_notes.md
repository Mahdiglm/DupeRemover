<div align="center">

# Pattern Exclusion Update v2.0.4

  <img src="https://img.shields.io/badge/pattern-exclusion-brightgreen" alt="Pattern exclusion"/>
  <img src="https://img.shields.io/badge/streaming-enhanced-blue" alt="Streaming enhanced"/>
  <img src="https://img.shields.io/badge/performance-improved-orange" alt="Performance improved"/>

<div style="border-left: 4px solid #5cb85c; padding-left: 15px; margin: 20px 0; color: #333;">
  This update introduces powerful pattern exclusion capabilities, allowing you to preserve specific lines from deduplication while enhancing streaming performance.
</div>

## New Features

<table>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>Exclude Pattern</strong>: Preserve lines matching regex patterns (<code>--exclude-pattern</code>)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Enhanced streaming mode with pattern exclusion support</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Optimized regex pattern compilation and caching for better performance</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Improved memory management for large files with pattern exclusion</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Comprehensive examples and documentation for pattern usage</td>
  </tr>
</table>

## Usage Examples

```bash
# Exclude lines beginning with timestamps
python main.py logs.txt --exclude-pattern "^[0-9]{4}-[0-9]{2}-[0-9]{2}"

# Preserve lines with log levels
python main.py data.txt --exclude-pattern "WARNING|ERROR|CRITICAL"

# Keep configuration comments
python main.py config.txt --exclude-pattern "^#.*$"
```

## Bug Fixes

<table>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Fixed indentation issues in try-except blocks</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Corrected memory leak with certain pattern combinations</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Improved error handling for malformed regex patterns</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Fixed edge case with empty line processing</td>
  </tr>
</table>

## Known Limitations

<table>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>Complex regex patterns may impact performance on very large files</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>Pattern matching occurs before fuzzy matching in fuzzy mode</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>UTF-16 encoded files may require special handling with certain patterns</td>
  </tr>
</table>

</div>
