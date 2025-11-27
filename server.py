#!/usr/bin/env python3
"""
browser-use Skill Server v2.0
Maintains browser session across multiple calls for Claude Code integration.
Updated for browser-use 2025 API (Page, Element, Mouse, CodeAgent)
"""

import asyncio
import json
import os
import sys
import socket
import signal
from pathlib import Path

# Server config
SERVER_PORT = 9223
PID_FILE = Path(__file__).parent / ".server.pid"
SOCKET_FILE = Path(__file__).parent / ".server.sock"


def is_server_running():
    """Check if server is running."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", SERVER_PORT))
        sock.close()
        if result == 0:
            return True
    except:
        pass

    if PID_FILE.exists():
        PID_FILE.unlink(missing_ok=True)
    return False


def send_command(cmd: dict) -> str:
    """Send command to running server."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(300)  # 5 min timeout for long tasks
        sock.connect(("127.0.0.1", SERVER_PORT))
        sock.sendall(json.dumps(cmd).encode() + b"\n")

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if response.endswith(b"\n"):
                break

        sock.close()
        return response.decode().strip()
    except Exception as e:
        return json.dumps({"error": str(e)})


class BrowserUseServer:
    """Server that maintains browser-use session."""

    def __init__(self):
        self.browser = None
        self.current_page = None
        self.llm = None
        self.running = False
        self._element_cache = {}  # Cache elements by index

    async def init_browser(self):
        """Initialize browser session."""
        if self.browser:
            return

        try:
            from browser_use import Browser

            self.browser = Browser(
                headless=False,
                highlight_elements=True,
            )
            await self.browser.start()
            print("Browser initialized", file=sys.stderr)
        except Exception as e:
            print(f"Browser init error: {e}", file=sys.stderr)
            raise

    async def get_current_page(self):
        """Get or create current page."""
        if not self.browser:
            await self.init_browser()

        if not self.current_page:
            self.current_page = await self.browser.get_current_page()
            if not self.current_page:
                self.current_page = await self.browser.new_page()

        return self.current_page

    async def init_llm(self):
        """Initialize LLM."""
        if self.llm:
            return

        try:
            # Try ChatBrowserUse first (recommended)
            try:
                from browser_use import ChatBrowserUse
                self.llm = ChatBrowserUse()
                print("LLM initialized (ChatBrowserUse)", file=sys.stderr)
                return
            except:
                pass

            # Try OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                from browser_use.llm.openai import ChatOpenAI
                self.llm = ChatOpenAI(model="gpt-4o", api_key=api_key)
                print("LLM initialized (OpenAI)", file=sys.stderr)
                return

            # Try Gemini
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if api_key:
                from browser_use.llm.google import ChatGoogle
                self.llm = ChatGoogle(model="gemini-1.5-flash", api_key=api_key)
                print("LLM initialized (Google)", file=sys.stderr)
                return

            # Try Ollama (local)
            try:
                from browser_use.llm.ollama import ChatOllama
                self.llm = ChatOllama(model="llama3")
                print("LLM initialized (Ollama)", file=sys.stderr)
                return
            except:
                pass

            print("Warning: No LLM configured. Set OPENAI_API_KEY or GEMINI_API_KEY", file=sys.stderr)
        except Exception as e:
            print(f"LLM init error: {e}", file=sys.stderr)

    async def handle_tool(self, tool: str, args: dict) -> dict:
        """Handle tool call."""
        try:
            # AI Agent tasks
            if tool == "run_agent":
                return await self._run_agent(
                    task=args.get("task", ""),
                    max_steps=args.get("max_steps", 10),
                    use_vision=args.get("use_vision", "auto"),
                    flash_mode=args.get("flash_mode", False),
                )

            if tool == "run_code_agent":
                return await self._run_code_agent(
                    task=args.get("task", ""),
                    max_steps=args.get("max_steps", 100),
                    use_vision=args.get("use_vision", True),
                )

            # Page-level tools
            page = await self.get_current_page()

            if tool == "navigate":
                return await self._navigate(args.get("url"), args.get("new_tab", False))
            elif tool == "go_back":
                return await self._go_back()
            elif tool == "go_forward":
                return await self._go_forward()
            elif tool == "reload":
                return await self._reload()
            elif tool == "get_state":
                return await self._get_state(args.get("include_screenshot", False))
            elif tool == "screenshot":
                return await self._screenshot(args.get("path", "screenshot.png"), args.get("format", "jpeg"), args.get("quality"))
            elif tool == "evaluate":
                return await self._evaluate(args.get("script"), args.get("args", []))
            elif tool == "press_key":
                return await self._press_key(args.get("key"))

            # Element tools
            elif tool == "find_elements":
                return await self._find_elements(args.get("selector"))
            elif tool == "find_element_by_prompt":
                return await self._find_element_by_prompt(args.get("prompt"))
            elif tool == "click":
                return await self._click(args.get("index"))
            elif tool == "type":
                return await self._type(args.get("index"), args.get("text"), args.get("clear", True))
            elif tool == "hover":
                return await self._hover(args.get("index"))
            elif tool == "check":
                return await self._check(args.get("index"))
            elif tool == "select_option":
                return await self._select_option(args.get("index"), args.get("value"))
            elif tool == "drag_to":
                return await self._drag_to(args.get("source_index"), args.get("target_index"))

            # Mouse tools
            elif tool == "mouse_click":
                return await self._mouse_click(args.get("x"), args.get("y"), args.get("button", "left"), args.get("click_count", 1))
            elif tool == "mouse_move":
                return await self._mouse_move(args.get("x"), args.get("y"))
            elif tool == "mouse_drag":
                return await self._mouse_drag(args.get("start_x"), args.get("start_y"), args.get("end_x"), args.get("end_y"))
            elif tool == "scroll":
                return await self._scroll(args.get("direction", "down"), args.get("amount", 500), args.get("x", 0), args.get("y", 0))

            # AI Features
            elif tool == "extract":
                return await self._extract(args.get("query"))
            elif tool == "extract_content":
                return await self._extract_content(args.get("prompt"), args.get("schema"))

            # Tab management
            elif tool == "list_tabs":
                return await self._list_tabs()
            elif tool == "switch_tab":
                return await self._switch_tab(args.get("tab_id"))
            elif tool == "close_tab":
                return await self._close_tab(args.get("tab_id"))
            elif tool == "close":
                return await self._close()
            else:
                return {"error": f"Unknown tool: {tool}"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    async def _run_agent(self, task: str, max_steps: int = 10, use_vision="auto", flash_mode: bool = False) -> dict:
        """Run AI agent to perform task."""
        await self.init_llm()
        if not self.llm:
            return {"error": "No LLM configured. Set OPENAI_API_KEY or GEMINI_API_KEY"}

        try:
            from browser_use import Agent, Browser

            browser = Browser(headless=False, highlight_elements=True)
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser,
                use_vision=use_vision,
                flash_mode=flash_mode,
            )

            history = await agent.run(max_steps=max_steps)

            result = {
                "success": history.is_successful(),
                "steps": history.number_of_steps(),
                "final_result": history.final_result(),
                "urls": [str(u) for u in history.urls() if u],
                "duration_seconds": history.total_duration_seconds(),
            }

            errors = history.errors()
            if errors:
                result["errors"] = [str(e) for e in errors if e]

            # Save final screenshot
            try:
                import base64
                from datetime import datetime
                screenshots = history.screenshots()
                if screenshots:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = Path(__file__).parent / f"agent_{timestamp}.png"
                    img_data = base64.b64decode(screenshots[-1])
                    screenshot_path.write_bytes(img_data)
                    result["screenshot_path"] = str(screenshot_path)
            except Exception as e:
                print(f"Screenshot save failed: {e}", file=sys.stderr)

            await browser.stop()
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    async def _run_code_agent(self, task: str, max_steps: int = 100, use_vision: bool = True) -> dict:
        """Run CodeAgent (Python code execution)."""
        await self.init_llm()
        if not self.llm:
            return {"error": "No LLM configured"}

        try:
            from browser_use import CodeAgent, Browser

            browser = Browser(headless=False, highlight_elements=True)
            agent = CodeAgent(
                task=task,
                llm=self.llm,
                browser=browser,
                use_vision=use_vision,
            )

            session = await agent.run(max_steps=max_steps)

            result = {
                "success": True,
                "cells_executed": session.current_execution_count if hasattr(session, 'current_execution_count') else 0,
            }

            await browser.stop()
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    async def _navigate(self, url: str, new_tab: bool = False) -> dict:
        """Navigate to URL."""
        if not url:
            return {"error": "URL required"}

        try:
            if new_tab:
                self.current_page = await self.browser.new_page(url)
            else:
                page = await self.get_current_page()
                await page.goto(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"error": str(e)}

    async def _go_back(self) -> dict:
        """Go back."""
        try:
            page = await self.get_current_page()
            await page.go_back()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def _go_forward(self) -> dict:
        """Go forward."""
        try:
            page = await self.get_current_page()
            await page.go_forward()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def _reload(self) -> dict:
        """Reload page."""
        try:
            page = await self.get_current_page()
            await page.reload()
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def _get_state(self, include_screenshot: bool = False) -> dict:
        """Get current page state."""
        try:
            page = await self.get_current_page()

            result = {
                "url": await page.get_url(),
                "title": await page.get_title(),
                "elements": []
            }

            # Get interactive elements via CSS selector
            try:
                selectors = "a, button, input, select, textarea, [onclick], [role='button']"
                elements = await page.get_elements_by_css_selector(selectors)
                self._element_cache = {}

                for idx, elem in enumerate(elements[:50]):  # Limit to 50 elements
                    try:
                        info = await elem.get_basic_info()
                        elem_info = {
                            "index": idx,
                            "tag": info.tag_name if hasattr(info, 'tag_name') else "unknown",
                            "text": (info.inner_text or "")[:100] if hasattr(info, 'inner_text') else "",
                        }
                        if hasattr(info, 'attributes'):
                            if info.attributes.get("placeholder"):
                                elem_info["placeholder"] = info.attributes["placeholder"]
                            if info.attributes.get("href"):
                                elem_info["href"] = info.attributes["href"][:50]
                        result["elements"].append(elem_info)
                        self._element_cache[idx] = elem
                    except:
                        pass
            except Exception as e:
                print(f"Element fetch error: {e}", file=sys.stderr)

            if include_screenshot:
                try:
                    import base64
                    from datetime import datetime
                    screenshot_b64 = await page.screenshot()
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = Path(__file__).parent / f"state_{timestamp}.png"
                    img_data = base64.b64decode(screenshot_b64)
                    screenshot_path.write_bytes(img_data)
                    result["screenshot_path"] = str(screenshot_path)
                except Exception as e:
                    print(f"Screenshot error: {e}", file=sys.stderr)

            return result
        except Exception as e:
            return {"error": str(e)}

    async def _screenshot(self, path: str, format: str = "jpeg", quality=None) -> dict:
        """Take screenshot."""
        try:
            page = await self.get_current_page()
            screenshot_b64 = await page.screenshot(format=format, quality=quality)
            import base64
            img_data = base64.b64decode(screenshot_b64)
            abs_path = Path(path).absolute()
            abs_path.write_bytes(img_data)
            return {"success": True, "path": str(abs_path)}
        except Exception as e:
            return {"error": str(e)}

    async def _evaluate(self, script: str, args: list = None) -> dict:
        """Execute JavaScript."""
        if not script:
            return {"error": "Script required"}

        try:
            page = await self.get_current_page()
            if args:
                result = await page.evaluate(script, *args)
            else:
                result = await page.evaluate(script)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}

    async def _press_key(self, key: str) -> dict:
        """Send keyboard input."""
        if not key:
            return {"error": "Key required"}

        try:
            page = await self.get_current_page()
            await page.press(key)
            return {"success": True, "key": key}
        except Exception as e:
            return {"error": str(e)}

    async def _find_elements(self, selector: str) -> dict:
        """Find elements by CSS selector."""
        if not selector:
            return {"error": "Selector required"}

        try:
            page = await self.get_current_page()
            elements = await page.get_elements_by_css_selector(selector)
            self._element_cache = {}

            result_elements = []
            for idx, elem in enumerate(elements[:50]):
                try:
                    info = await elem.get_basic_info()
                    result_elements.append({
                        "index": idx,
                        "tag": info.tag_name if hasattr(info, 'tag_name') else "unknown",
                        "text": (info.inner_text or "")[:100] if hasattr(info, 'inner_text') else "",
                    })
                    self._element_cache[idx] = elem
                except:
                    pass

            return {"success": True, "count": len(elements), "elements": result_elements}
        except Exception as e:
            return {"error": str(e)}

    async def _find_element_by_prompt(self, prompt: str) -> dict:
        """Find element using natural language (LLM-powered)."""
        if not prompt:
            return {"error": "Prompt required"}

        await self.init_llm()
        if not self.llm:
            return {"error": "No LLM configured"}

        try:
            page = await self.get_current_page()
            element = await page.get_element_by_prompt(prompt, llm=self.llm)

            if element:
                info = await element.get_basic_info()
                self._element_cache[0] = element  # Store at index 0
                return {
                    "success": True,
                    "found": True,
                    "index": 0,
                    "tag": info.tag_name if hasattr(info, 'tag_name') else "unknown",
                    "text": (info.inner_text or "")[:100] if hasattr(info, 'inner_text') else "",
                }
            else:
                return {"success": True, "found": False}
        except Exception as e:
            return {"error": str(e)}

    async def _click(self, index: int) -> dict:
        """Click element by index."""
        if index is None:
            return {"error": "Index required"}

        try:
            if index in self._element_cache:
                elem = self._element_cache[index]
                await elem.click()
                return {"success": True, "clicked_index": index}
            else:
                return {"error": f"Element {index} not in cache. Call find_elements or get_state first"}
        except Exception as e:
            return {"error": str(e)}

    async def _type(self, index: int, text: str, clear: bool = True) -> dict:
        """Type text into element."""
        if index is None:
            return {"error": "Index required"}
        if not text:
            return {"error": "Text required"}

        try:
            if index in self._element_cache:
                elem = self._element_cache[index]
                await elem.fill(text, clear=clear)
                return {"success": True, "typed": text}
            else:
                return {"error": f"Element {index} not in cache"}
        except Exception as e:
            return {"error": str(e)}

    async def _hover(self, index: int) -> dict:
        """Hover over element."""
        if index is None:
            return {"error": "Index required"}

        try:
            if index in self._element_cache:
                elem = self._element_cache[index]
                await elem.hover()
                return {"success": True, "hovered_index": index}
            else:
                return {"error": f"Element {index} not in cache"}
        except Exception as e:
            return {"error": str(e)}

    async def _check(self, index: int) -> dict:
        """Toggle checkbox/radio."""
        if index is None:
            return {"error": "Index required"}

        try:
            if index in self._element_cache:
                elem = self._element_cache[index]
                await elem.check()
                return {"success": True, "checked_index": index}
            else:
                return {"error": f"Element {index} not in cache"}
        except Exception as e:
            return {"error": str(e)}

    async def _select_option(self, index: int, value) -> dict:
        """Select dropdown option."""
        if index is None:
            return {"error": "Index required"}
        if value is None:
            return {"error": "Value required"}

        try:
            if index in self._element_cache:
                elem = self._element_cache[index]
                await elem.select_option(value)
                return {"success": True, "selected": value}
            else:
                return {"error": f"Element {index} not in cache"}
        except Exception as e:
            return {"error": str(e)}

    async def _drag_to(self, source_index: int, target_index: int) -> dict:
        """Drag element to another."""
        if source_index is None or target_index is None:
            return {"error": "source_index and target_index required"}

        try:
            if source_index in self._element_cache and target_index in self._element_cache:
                source = self._element_cache[source_index]
                target = self._element_cache[target_index]
                await source.drag_to(target)
                return {"success": True, "dragged": source_index, "to": target_index}
            else:
                return {"error": "Elements not in cache"}
        except Exception as e:
            return {"error": str(e)}

    async def _mouse_click(self, x: int, y: int, button: str = "left", click_count: int = 1) -> dict:
        """Click at coordinates."""
        if x is None or y is None:
            return {"error": "x and y required"}

        try:
            page = await self.get_current_page()
            mouse = page.mouse
            await mouse.click(x=x, y=y, button=button, click_count=click_count)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"error": str(e)}

    async def _mouse_move(self, x: int, y: int) -> dict:
        """Move mouse to coordinates."""
        if x is None or y is None:
            return {"error": "x and y required"}

        try:
            page = await self.get_current_page()
            mouse = page.mouse
            await mouse.move(x=x, y=y)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"error": str(e)}

    async def _mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> dict:
        """Drag from one position to another."""
        if None in [start_x, start_y, end_x, end_y]:
            return {"error": "start_x, start_y, end_x, end_y required"}

        try:
            page = await self.get_current_page()
            mouse = page.mouse
            await mouse.down()
            await mouse.move(x=start_x, y=start_y)
            await mouse.move(x=end_x, y=end_y)
            await mouse.up()
            return {"success": True, "from": [start_x, start_y], "to": [end_x, end_y]}
        except Exception as e:
            return {"error": str(e)}

    async def _scroll(self, direction: str = "down", amount: int = 500, x: int = 0, y: int = 0) -> dict:
        """Scroll page."""
        try:
            page = await self.get_current_page()
            mouse = page.mouse
            delta_y = -amount if direction == "up" else amount
            await mouse.scroll(x=x, y=y, delta_y=delta_y)
            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            return {"error": str(e)}

    async def _extract(self, query: str) -> dict:
        """Extract content using LLM."""
        if not query:
            return {"error": "Query required"}

        await self.init_llm()
        if not self.llm:
            return {"error": "No LLM configured"}

        try:
            page = await self.get_current_page()
            url = await page.get_url()
            title = await page.get_title()
            return {"content": f"Page: {title}\nURL: {url}\n(Use run_agent with extract task for intelligent extraction)"}
        except Exception as e:
            return {"error": str(e)}

    async def _extract_content(self, prompt: str, schema: dict = None) -> dict:
        """Extract structured content using LLM."""
        if not prompt:
            return {"error": "Prompt required"}

        await self.init_llm()
        if not self.llm:
            return {"error": "No LLM configured"}

        try:
            page = await self.get_current_page()

            # Create dynamic Pydantic model if schema provided
            if schema:
                from pydantic import create_model
                fields = {}
                for key, type_str in schema.items():
                    if type_str == "string":
                        fields[key] = (str, ...)
                    elif type_str == "number":
                        fields[key] = (float, ...)
                    elif type_str == "int":
                        fields[key] = (int, ...)
                    elif type_str == "bool":
                        fields[key] = (bool, ...)
                    else:
                        fields[key] = (str, ...)

                DynamicModel = create_model("DynamicModel", **fields)
                result = await page.extract_content(prompt, DynamicModel, self.llm)
                return {"success": True, "data": result.model_dump()}
            else:
                # Simple extraction without schema
                url = await page.get_url()
                title = await page.get_title()
                return {"success": True, "url": url, "title": title, "note": "Provide schema for structured extraction"}
        except Exception as e:
            return {"error": str(e)}

    async def _list_tabs(self) -> dict:
        """List tabs."""
        try:
            pages = await self.browser.get_pages()
            tabs = []
            for i, page in enumerate(pages):
                tabs.append({
                    "index": i,
                    "url": await page.get_url(),
                    "title": await page.get_title(),
                })
            return {"tabs": tabs}
        except Exception as e:
            return {"error": str(e)}

    async def _switch_tab(self, tab_id) -> dict:
        """Switch tab by index."""
        if tab_id is None:
            return {"error": "tab_id (index) required"}

        try:
            pages = await self.browser.get_pages()
            idx = int(tab_id)
            if 0 <= idx < len(pages):
                self.current_page = pages[idx]
                return {"success": True, "switched_to": idx}
            else:
                return {"error": f"Tab index {idx} out of range"}
        except Exception as e:
            return {"error": str(e)}

    async def _close_tab(self, tab_id) -> dict:
        """Close tab by index."""
        if tab_id is None:
            return {"error": "tab_id (index) required"}

        try:
            pages = await self.browser.get_pages()
            idx = int(tab_id)
            if 0 <= idx < len(pages):
                await self.browser.close_page(pages[idx])
                self.current_page = None
                return {"success": True, "closed": idx}
            else:
                return {"error": f"Tab index {idx} out of range"}
        except Exception as e:
            return {"error": str(e)}

    async def _close(self) -> dict:
        """Close browser."""
        try:
            if self.browser:
                await self.browser.stop()
                self.browser = None
                self.current_page = None
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def handle_client(self, reader, writer):
        """Handle client connection."""
        try:
            data = await reader.readline()
            if not data:
                return

            cmd = json.loads(data.decode())

            if cmd.get("action") == "status":
                result = {"status": "running", "browser": self.browser is not None}
            elif cmd.get("action") == "stop":
                self.running = False
                result = {"status": "stopping"}
            elif cmd.get("tool"):
                result = await self.handle_tool(cmd["tool"], cmd.get("args", {}))
            else:
                result = {"error": "Invalid command"}

            writer.write(json.dumps(result).encode() + b"\n")
            await writer.drain()
        except Exception as e:
            try:
                writer.write(json.dumps({"error": str(e)}).encode() + b"\n")
                await writer.drain()
            except:
                pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def run(self):
        """Run the server."""
        self.running = True
        server = await asyncio.start_server(
            self.handle_client, "127.0.0.1", SERVER_PORT
        )

        PID_FILE.write_text(str(os.getpid()))
        print(f"browser-use server v2.0 started on port {SERVER_PORT}", file=sys.stderr)

        async with server:
            while self.running:
                await asyncio.sleep(0.1)

        await self._close()
        PID_FILE.unlink(missing_ok=True)
        print("Server stopped", file=sys.stderr)


def start_server():
    """Start the server."""
    if is_server_running():
        print("Server already running")
        return

    server = BrowserUseServer()

    def signal_handler(sig, frame):
        server.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(server.run())


def stop_server():
    """Stop the server."""
    if not is_server_running():
        print("Server not running")
        return

    result = send_command({"action": "stop"})
    print(result)


def get_status():
    """Get server status."""
    if not is_server_running():
        print(json.dumps({"status": "not running"}))
        return

    result = send_command({"action": "status"})
    print(result)


def call_tool(cmd_json: str):
    """Call a tool."""
    if not is_server_running():
        print(json.dumps({"error": "Server not running. Run: python server.py start &"}))
        return

    try:
        cmd = json.loads(cmd_json)
        result = send_command(cmd)
        print(result)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))


def main():
    if len(sys.argv) < 2:
        print("""
browser-use Skill Server v2.0

Usage:
  python server.py start     # Start server (use & for background)
  python server.py stop      # Stop server
  python server.py status    # Check status
  python server.py call '{"tool": "...", "args": {...}}'

Tools:
  AI Agents:
    run_agent        - AI agent (task, max_steps, use_vision, flash_mode)
    run_code_agent   - Python code agent (task, max_steps, use_vision)

  Page:
    navigate, go_back, go_forward, reload, get_state, screenshot, evaluate, press_key

  Element:
    find_elements, find_element_by_prompt, click, type, hover, check, select_option, drag_to

  Mouse:
    mouse_click, mouse_move, mouse_drag, scroll

  AI Features:
    extract, extract_content

  Tabs:
    list_tabs, switch_tab, close_tab, close

Examples:
  python server.py start &
  python server.py call '{"tool": "run_agent", "args": {"task": "Search Google for AI news", "flash_mode": true}}'
  python server.py call '{"tool": "navigate", "args": {"url": "https://google.com"}}'
  python server.py call '{"tool": "find_element_by_prompt", "args": {"prompt": "search box"}}'
  python server.py call '{"tool": "mouse_click", "args": {"x": 100, "y": 200}}'
""")
        return

    cmd = sys.argv[1]

    if cmd == "start":
        start_server()
    elif cmd == "stop":
        stop_server()
    elif cmd == "status":
        get_status()
    elif cmd == "call":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing JSON argument"}))
        else:
            call_tool(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
