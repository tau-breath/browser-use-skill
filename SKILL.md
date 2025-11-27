# browser-use Skill for Claude Code

A wrapper around the official [browser-use](https://github.com/browser-use/browser-use) library that enables Claude Code to perform browser automation tasks through two modes: Direct Mode (Claude controls browser directly) and Subagent Mode (autonomous agent execution).

## Features

- **Direct Mode**: Claude directly controls browser via Actor API (no external LLM API key required!)
- **Subagent Mode**: Delegate complex browser tasks to autonomous subagents
- **Session Persistence**: Server mode keeps browser session alive across multiple calls
- **Full Automation**: Navigate, click, type, screenshot, scroll, and more
- **Bot Detection Bypass**: Uses browser-use's stealth capabilities

## Triggers

**AI Automation Requests:**
- "browse to...", "open website..."
- "search for...", "find on web..."
- "fill out form...", "automate..."
- "web research...", "scrape..."
- "take screenshot of..."

**Development Testing:**
- localhost URLs
- QA automation
- E2E testing

## Installation

### 1. Install browser-use

```bash
pip install browser-use
playwright install chromium
```

### 2. Copy skill to Claude Code

```bash
cp -r browser-use-skill ~/.claude/skills/browser-use
```

### 3. Start server

```bash
cd ~/.claude/skills/browser-use
python server.py start &
```

## Quick Start

### Direct Mode (Recommended - No API Key Required!)

Claude directly controls the browser step by step:

```bash
cd ~/.claude/skills/browser-use

# Start server
python server.py start &
sleep 2

# Navigate to page
python server.py call '{"tool": "navigate", "args": {"url": "https://google.com"}}'

# Get page state with screenshot
python server.py call '{"tool": "get_state", "args": {"include_screenshot": true}}'
# Returns: elements list + screenshot_path (read with Vision!)

# Click element by index (from get_state)
python server.py call '{"tool": "click", "args": {"index": 0}}'

# Type text
python server.py call '{"tool": "type", "args": {"index": 0, "text": "search query"}}'

# Press Enter
python server.py call '{"tool": "press_key", "args": {"key": "Enter"}}'

# Take screenshot
python server.py call '{"tool": "screenshot", "args": {"path": "result.png"}}'
```

### Subagent Mode

Delegate browser tasks to Claude Code subagents:

```
Use Task tool with subagent_type: "general-purpose"

Prompt template:
"Browser automation task using browser-use skill (Direct Mode).
Goal: [your task]
Server already running on port 9223.
Workflow: get_state -> analyze screenshot -> click/type -> repeat until done"
```

## Server Commands

```bash
python server.py start     # Start server (use & for background)
python server.py stop      # Stop server
python server.py status    # Check status
python server.py call '{"tool": "...", "args": {...}}'
```

## Tool Reference

### Page Tools

| Tool | Description | Args |
|------|-------------|------|
| navigate | Go to URL | url, new_tab |
| go_back | Navigate back | - |
| go_forward | Navigate forward | - |
| reload | Refresh page | - |
| get_state | Get page state + elements | include_screenshot |
| screenshot | Save screenshot | path, format, quality |
| evaluate | Run JavaScript | script, args |
| press_key | Keyboard input | key |

### Element Tools

| Tool | Description | Args |
|------|-------------|------|
| find_elements | Find by CSS selector | selector |
| click | Click element | index |
| type | Type into input | index, text, clear |
| hover | Mouse hover | index |
| check | Toggle checkbox | index |
| select_option | Select dropdown | index, value |
| drag_to | Drag and drop | source_index, target_index |

### Mouse Tools

| Tool | Description | Args |
|------|-------------|------|
| mouse_click | Click at coordinates | x, y, button, click_count |
| mouse_move | Move mouse | x, y |
| mouse_drag | Drag from A to B | start_x, start_y, end_x, end_y |
| scroll | Scroll page | direction, amount, x, y |

### Tab Management

| Tool | Description | Args |
|------|-------------|------|
| list_tabs | List open tabs | - |
| switch_tab | Switch to tab | tab_id (index) |
| close_tab | Close tab | tab_id (index) |
| close | Close browser | - |

### AI Agent Tools (Requires API Key)

| Tool | Description | Args |
|------|-------------|------|
| run_agent | AI agent execution | task, max_steps, use_vision, flash_mode |
| run_code_agent | Python code agent | task, max_steps, use_vision |

## Examples

### Example 1: Google Search (Direct Mode)

```bash
cd ~/.claude/skills/browser-use
python server.py start &
sleep 2

# Open Google
python server.py call '{"tool": "navigate", "args": {"url": "https://google.com"}}'

# Get elements
python server.py call '{"tool": "get_state", "args": {"include_screenshot": true}}'

# Type search query (index 0 is usually search box)
python server.py call '{"tool": "type", "args": {"index": 0, "text": "Claude AI"}}'

# Press Enter
python server.py call '{"tool": "press_key", "args": {"key": "Enter"}}'

# Screenshot results
python server.py call '{"tool": "screenshot", "args": {"path": "google_results.png"}}'
```

### Example 2: Form Filling

```bash
# Navigate to form
python server.py call '{"tool": "navigate", "args": {"url": "https://example.com/form"}}'

# Get form elements
python server.py call '{"tool": "get_state", "args": {"include_screenshot": true}}'

# Fill fields (use indices from get_state)
python server.py call '{"tool": "type", "args": {"index": 0, "text": "John Doe"}}'
python server.py call '{"tool": "type", "args": {"index": 1, "text": "john@example.com"}}'

# Submit
python server.py call '{"tool": "click", "args": {"index": 5}}'
```

### Example 3: Coordinate Click (When Index Fails)

```bash
# Get screenshot first
python server.py call '{"tool": "get_state", "args": {"include_screenshot": true}}'

# Analyze screenshot with Vision, then click at coordinates
python server.py call '{"tool": "mouse_click", "args": {"x": 500, "y": 300}}'
```

### Example 4: Keyboard Navigation

```bash
# Tab through elements
python server.py call '{"tool": "press_key", "args": {"key": "Tab"}}'
python server.py call '{"tool": "press_key", "args": {"key": "Tab"}}'
python server.py call '{"tool": "press_key", "args": {"key": "Enter"}}'

# Keyboard shortcuts
python server.py call '{"tool": "press_key", "args": {"key": "Control+a"}}'  # Select all
python server.py call '{"tool": "press_key", "args": {"key": "Control+c"}}'  # Copy
```

## Troubleshooting

### "Server not running" error

```bash
python server.py start &
sleep 2
python server.py status
```

### Element click not working

1. Re-fetch elements: `get_state` with `include_screenshot: true`
2. Check correct index in elements list
3. Try keyboard navigation: `press_key("Tab")` then `press_key("Enter")`
4. Use coordinate click: `mouse_click(x, y)`

### Elements showing as "unknown"

This is normal for complex pages. The element cache still works - use the index to click/type.

### Browser not visible

Server runs headless by default in background. Browser window appears but may be behind other windows.

### Session disconnected

Always use `server.py` (server mode). Each `server.py call` maintains the same session.

## How It Works

### Why Server Mode?

Without server mode, each Python call would:
1. Launch browser
2. Perform action
3. Close browser (lose state!)

With server mode:
1. Start server once (browser stays open)
2. All calls share same browser session
3. Stop server when done

### Direct Mode vs Subagent Mode

**Direct Mode:**
- Claude reads screenshot (Vision)
- Claude decides next action
- Claude calls tool
- Repeat until done

**Subagent Mode:**
- Claude spawns subagent with task description
- Subagent autonomously navigates
- Subagent reports results
- Better for complex multi-step tasks

## Requirements

- Python 3.8+
- browser-use library
- Playwright + Chromium
- (Optional) LLM API key for run_agent/run_code_agent tools

## License

MIT

---

## DPA - Decentralized Protection Alliance

**Freedom without surveillance, protection for everyone.**

[dpa.network](https://dpa.network) | [contact@dpa.network](mailto:contact@dpa.network) | [Matrix](https://matrix.to/#/#dpa_network:matrix.org) | [Telegram](https://t.me/dpa_network)
