<div align="center">

# GUI + PyInstaller Update v2.11.0

  <img src="https://img.shields.io/badge/pyside6-gui-brightgreen" alt="PySide6 GUI"/>
  <img src="https://img.shields.io/badge/pyinstaller-ready-blue" alt="PyInstaller ready"/>
  <img src="https://img.shields.io/badge/windows-exe-orange" alt="Windows exe"/>

<div style="border-left: 4px solid #5cb85c; padding-left: 15px; margin: 20px 0; color: #333;">
  This update introduces a full PySide6 GUI (batch + streaming), adds a GUI/CLI launcher entrypoint, and includes PyInstaller support for building a Windows executable.
</div>

## New Features

<table>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>PySide6 GUI</strong>: New graphical interface with Batch and Streaming tabs (<code>pyside_gui.py</code>)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>GUI/CLI Launcher</strong>: New <code>app.py</code> entrypoint lets you choose GUI or classic CLI at startup (CLI fallback if PySide6 is not available)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>PyInstaller Support</strong>: Added <code>duperemover.spec</code> and <code>build_exe.ps1</code> to build a Windows executable (includes PySide6 hidden imports)</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>Dependencies File</strong>: Added <code>requirements.txt</code> including PySide6 + PyInstaller</td>
  </tr>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td><strong>Test Suite</strong>: Added unit tests for core deduplication and reporting (<code>test_duplicate_remover.py</code>)</td>
  </tr>
</table>

## Usage Examples

```bash
# Launch and choose GUI or CLI
python app.py

# Build a Windows executable (PowerShell)
powershell -ExecutionPolicy Bypass -File build_exe.ps1

# CLI: show a full-screen live dashboard while processing a big file
python main.py large_file.txt --dashboard

# CLI: real-time log cleaning with a live dashboard
python main.py server.log --stream --follow --dashboard

# CLI: save unique streamed lines to a file instead of stdout
python main.py server.log --stream --follow --stream-output unique.log

# CLI: generate a quick HTML report
python main.py logs.txt --report html --report-file report.html
```

## Bug Fixes

<table>
  <tr>
    <td width="40" align="center"><strong>✓</strong></td>
    <td>Version and release metadata updated to match v2.11.0 (CLI + docs + GUI title)</td>
  </tr>
</table>

## Known Limitations

<table>
  <tr>
    <td width="40" align="center"><strong>!</strong></td>
    <td>PyInstaller build uses <code>console=True</code> (the executable opens with a console window)</td>
  </tr>
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
