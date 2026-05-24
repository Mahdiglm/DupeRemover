<div align="center">

# Live Dashboard Update v2.10.0

  <img src="https://img.shields.io/badge/live-dashboard-brightgreen" alt="Live dashboard"/>
  <img src="https://img.shields.io/badge/streaming-upgraded-blue" alt="Streaming upgraded"/>
  <img src="https://img.shields.io/badge/reports-complete-orange" alt="Reports complete"/>

<div style="border-left: 4px solid #5cb85c; padding-left: 15px; margin: 20px 0; color: #333;">
  This update adds a full-screen live terminal dashboard and improved streaming output control, plus completes the report formats advertised by the CLI.
</div>

## New Features

<table>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>Live Dashboard</strong>: Full-screen live view with speed, totals, and duplication rate (<code>--dashboard</code>)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Streaming dashboard shows latest unique lines in real time (<code>--stream --follow --dashboard</code>)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>Stream Output Target</strong>: Write unique streamed lines to a file (<code>--stream-output</code>)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>Report Formats Completed</strong>: Fully implemented <code>text</code>, <code>json</code>, <code>csv</code>, <code>html</code>, <code>xml</code>, <code>yaml</code>, <code>markdown</code></td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Optional progress UI fallback when <code>tqdm</code> is not installed (runs without crashing)</td>
  </tr>
</table>

## Usage Examples

```bash
# Show a full-screen live dashboard while processing a big file
python main.py large_file.txt --dashboard

# Real-time log cleaning with a live dashboard
python main.py server.log --stream --follow --dashboard

# Save unique streamed lines to a file instead of stdout
python main.py server.log --stream --follow --stream-output unique.log

# Generate a quick HTML report
python main.py logs.txt --report html --report-file report.html
```

## Bug Fixes

<table>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Fixed cross-chunk deduplication so duplicates spanning chunk boundaries are removed correctly</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Fixed multiple CLI/runtime crashes caused by missing flags and report function mismatches</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Hardened report generation when some processed files return error records</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Improved streaming output behavior (proper newlines and optional file output)</td>
  </tr>
</table>

## Known Limitations

<table>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>Full-screen dashboard uses ANSI escape sequences; some terminals may render it imperfectly</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>When <code>--dashboard</code> is enabled, per-line progress indicators are suppressed for a cleaner UI</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>Very high-velocity log files may require tuning <code>--poll-interval</code> and using <code>--stream-output</code></td>
  </tr>
</table>

</div>
