# browser-use Skill for Claude Code

A Claude Code skill that wraps the official [browser-use](https://github.com/browser-use/browser-use) library, enabling AI-powered browser automation through two modes:

1. **Direct Mode** - Claude directly controls browser via Actor API (no external LLM API key required!)
2. **Subagent Mode** - Delegate complex tasks to autonomous Claude Code subagents

## Why This Skill?

The official browser-use library is designed for standalone Python scripts with LLM integration. This skill adapts it for Claude Code by:

- **Server Mode**: Maintains browser session across multiple tool calls
- **Direct Control**: Claude can control browser step-by-step using Vision
- **No API Key Required**: Direct Mode works without OpenAI/Gemini API keys
- **Session Persistence**: Browser stays open until explicitly closed

## Features

- Navigate to any URL
- Click elements by index or coordinates
- Type text into forms
- Take screenshots (Vision-compatible)
- Keyboard input and shortcuts
- Scroll and mouse actions
- Tab management
- JavaScript evaluation

## Installation

### 1. Install dependencies

```bash
pip install browser-use
playwright install chromium
```

### 2. Copy skill to Claude Code

```bash
# Clone this repo
git clone https://github.com/tau-breath/browser-use-skill.git

# Copy to Claude Code skills directory
cp -r browser-use-skill ~/.claude/skills/browser-use
```

### 3. Verify installation

```bash
cd ~/.claude/skills/browser-use
python server.py start &
sleep 2
python server.py status
python server.py stop
```

## Quick Start

### Direct Mode (No API Key Required!)

```bash
cd ~/.claude/skills/browser-use

# Start server (keep running in background)
python server.py start &
sleep 2

# Navigate
python server.py call '{"tool": "navigate", "args": {"url": "https://google.com"}}'

# Get page state with screenshot
python server.py call '{"tool": "get_state", "args": {"include_screenshot": true}}'

# Type into search box (index from get_state)
python server.py call '{"tool": "type", "args": {"index": 0, "text": "Claude AI"}}'

# Press Enter
python server.py call '{"tool": "press_key", "args": {"key": "Enter"}}'

# Screenshot results
python server.py call '{"tool": "screenshot", "args": {"path": "results.png"}}'

# Stop server when done
python server.py stop
```

## Server Commands

| Command | Description |
|---------|-------------|
| `python server.py start &` | Start server in background |
| `python server.py stop` | Stop server |
| `python server.py status` | Check server status |
| `python server.py call '{...}'` | Call a tool |

## Available Tools

### Page Tools
- `navigate` - Go to URL
- `go_back` / `go_forward` - Navigation history
- `reload` - Refresh page
- `get_state` - Get elements + optional screenshot
- `screenshot` - Save screenshot to file
- `evaluate` - Run JavaScript
- `press_key` - Keyboard input

### Element Tools
- `find_elements` - Find by CSS selector
- `click` - Click element by index
- `type` - Type text into element
- `hover` - Mouse hover
- `check` - Toggle checkbox
- `select_option` - Select dropdown option
- `drag_to` - Drag and drop

### Mouse Tools
- `mouse_click` - Click at coordinates
- `mouse_move` - Move mouse
- `mouse_drag` - Drag from A to B
- `scroll` - Scroll page

### Tab Management
- `list_tabs` - List open tabs
- `switch_tab` - Switch to tab
- `close_tab` - Close tab
- `close` - Close browser

## Example: Search Naver (Korean Portal)

```bash
# Start server
cd ~/.claude/skills/browser-use && python server.py start &
sleep 2

# Navigate to Naver search
python server.py call '{"tool": "navigate", "args": {"url": "https://search.naver.com/search.naver?query=Claude+AI"}}'

# Get screenshot
python server.py call '{"tool": "get_state", "args": {"include_screenshot": true}}'
# Returns: {"url": "...", "elements": [...], "screenshot_path": "/path/to/screenshot.png"}

# Read screenshot with Vision to analyze results
```

## Troubleshooting

### Server not running
```bash
python server.py start &
sleep 2
```

### Element click not working
1. Use `get_state` to refresh element cache
2. Try `press_key("Tab")` then `press_key("Enter")`
3. Use `mouse_click(x, y)` with coordinates from screenshot

### Session lost
Always use `server.py` commands. Direct Python calls don't maintain session.

## How It Works

```
Without Server Mode:
  Call 1: navigate -> opens browser -> closes on exit (state lost!)
  Call 2: click -> ERROR: no browser!

With Server Mode:
  Start server: browser session created
  Call 1: navigate -> works
  Call 2: click -> works (same session!)
  Call N: ... -> works
  Stop server: browser closes
```

## Requirements

- Python 3.8+
- browser-use (`pip install browser-use`)
- Playwright + Chromium (`playwright install chromium`)
- (Optional) LLM API key for `run_agent` tool

## License

MIT

## Credits

- [browser-use](https://github.com/browser-use/browser-use) - The official browser automation library

---

## DPA - Decentralized Protection Alliance

**Freedom without surveillance, protection for everyone.**

[dpa.network](https://dpa.network) | [contact@dpa.network](mailto:contact@dpa.network) | [Matrix](https://matrix.to/#/#dpa_network:matrix.org) | [Telegram](https://t.me/dpa_network)
