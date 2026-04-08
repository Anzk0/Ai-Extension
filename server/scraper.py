#!/usr/bin/env python3
"""
Blackboard Ultra content scraper for University of Salford.

Downloads content files from all modules and organises them
into your Obsidian vault by module name.

Usage:
    1. Close Microsoft Edge completely
    2. cd browser-ai-assistant/server
    3. python scraper.py

Files are saved to: vault_path/<ModuleName>/<filename>
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BLACKBOARD_URL = 'https://blackboard.salford.ac.uk/ultra/course'
EDGE_USER_DATA = r'C:\Users\khanp\AppData\Local\Microsoft\Edge\User Data'

# Tab / section names to SKIP — anything assessment/admin related
SKIP_KEYWORDS = {
    'assignment', 'assignments', 'assessment', 'assessments',
    'grade', 'grades', 'gradebook', 'test', 'tests',
    'quiz', 'quizzes', 'discussion', 'discussions',
    'group', 'groups', 'calendar', 'announcement', 'announcements',
    'roster', 'attendance', 'email', 'messages', 'journal',
    'blog', 'wiki', 'collaboration'
}

# File extensions we want to download
CONTENT_EXTENSIONS = re.compile(
    r'\.(pdf|pptx?|docx?|xlsx?|zip|txt|mp4|mp3|png|jpg|jpeg)$',
    re.IGNORECASE
)


def safe_folder_name(name: str) -> str:
    """Strip characters that are invalid in Windows folder names."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:80]  # cap length


def is_skip_section(name: str) -> bool:
    """Return True if this section/tab should be skipped."""
    lower = name.lower()
    return any(kw in lower for kw in SKIP_KEYWORDS)


async def find_and_download_files(page, module_folder: Path) -> int:
    """
    On the current Blackboard page, find all downloadable content files
    and save them to module_folder. Returns count of downloaded files.
    """
    downloaded = 0

    # Wait for content to load
    await page.wait_for_load_state('networkidle', timeout=15000)

    # Collect all links that look like files
    links = await page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a[href]'))
            .map(a => ({
                href: a.href,
                text: (a.textContent || a.getAttribute("aria-label") || "").trim()
            }))
            .filter(l => l.href && !l.href.startsWith("javascript"));
    }''')

    for link in links:
        href = link['href']
        text = link['text'] or 'file'

        # Only download if it looks like a content file
        is_content_url = (
            CONTENT_EXTENSIONS.search(href)
            or '/bbcswebdav/' in href
            or '/xapi/orion/file' in href
            or 'bboffice' in href.lower()
        )

        if not is_content_url:
            continue

        # Skip if the link text suggests it's an assessment
        if is_skip_section(text):
            continue

        try:
            async with page.expect_download(timeout=20000) as dl_info:
                # Open the link — Blackboard usually triggers a download
                new_page = await page.context.new_page()
                await new_page.goto(href)
                try:
                    download = await dl_info.value
                    filename = download.suggested_filename
                    if not filename:
                        filename = safe_folder_name(text) + '.pdf'
                    save_path = module_folder / filename
                    # Don't overwrite existing files
                    if not save_path.exists():
                        await download.save_as(str(save_path))
                        print(f"    ✅  {filename}")
                        downloaded += 1
                    else:
                        print(f"    ⏭️  Already exists: {filename}")
                finally:
                    await new_page.close()
        except PlaywrightTimeout:
            # Not a direct download — try navigating and looking for embedded files
            pass
        except Exception as e:
            print(f"    ⚠️  Could not download '{text}': {type(e).__name__}")

    return downloaded


async def scrape_module(context, module_name: str, module_url: str, vault_path: str) -> int:
    """Open a module, walk its content sections, and download files."""
    folder_name = safe_folder_name(module_name)
    module_folder = Path(vault_path) / folder_name
    module_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n  📚  {module_name}")
    page = await context.new_page()
    total = 0

    try:
        await page.goto(module_url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_load_state('networkidle', timeout=15000)

        # Find left-nav sections / tabs inside the module
        sections = await page.evaluate('''() => {
            const items = Array.from(document.querySelectorAll(
                "ul.courseSectionList li a, nav a, [role='navigation'] a, " +
                "[class*='left-nav'] a, [class*='sidebar'] a, [class*='menu'] a"
            ));
            return items.map(a => ({
                text: (a.textContent || a.getAttribute("aria-label") || "").trim(),
                href: a.href
            })).filter(i => i.text && i.href && !i.href.startsWith("javascript"));
        }''')

        content_sections = [s for s in sections if not is_skip_section(s['text'])]

        if content_sections:
            for section in content_sections:
                print(f"      → Section: {section['text']}")
                section_folder = module_folder / safe_folder_name(section['text'])
                section_folder.mkdir(parents=True, exist_ok=True)
                await page.goto(section['href'], wait_until='domcontentloaded', timeout=15000)
                count = await find_and_download_files(page, section_folder)
                total += count
                # Remove empty section folder
                if not any(section_folder.iterdir()):
                    section_folder.rmdir()
        else:
            # No nav sections found — try downloading from current page directly
            total += await find_and_download_files(page, module_folder)

    except Exception as e:
        print(f"      ⚠️  Error processing module: {e}")
    finally:
        await page.close()

    print(f"      → {total} file(s) saved")
    return total


async def get_modules(page) -> list:
    """Extract all module names and URLs from the Blackboard course list page."""
    await page.goto(BLACKBOARD_URL, wait_until='domcontentloaded', timeout=20000)
    await page.wait_for_load_state('networkidle', timeout=15000)

    # Check if we got redirected to login
    if 'login' in page.url.lower() or 'webapps/login' in page.url.lower():
        print("\n⚠️  Not logged in. A browser window is open — please log in manually.")
        print("   Press Enter here once you're on the Blackboard course page...")
        input()
        await page.wait_for_load_state('networkidle', timeout=30000)

    modules = await page.evaluate('''() => {
        // Blackboard Ultra: course cards link to /ultra/courses/<id>/cl/outline
        const links = Array.from(document.querySelectorAll('a[href*="/ultra/courses/"]'));
        const seen = new Set();
        const results = [];
        for (const a of links) {
            const href = a.href.split("?")[0];  // strip query params
            if (seen.has(href)) continue;
            seen.add(href);
            const name = (
                a.getAttribute("aria-label") ||
                a.querySelector("[class*='name'], [class*='title'], h3, h4, span")?.textContent ||
                a.textContent
            ).trim().replace(/\\s+/g, " ");
            if (name) results.push({ name, url: href });
        }
        return results;
    }''')

    return modules


async def main():
    # Load config
    config_path = Path(__file__).parent / 'config.json'
    if not config_path.exists():
        print("❌ config.json not found. Copy config.example.json to config.json and fill in your vault_path.")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    vault_path = config.get('vault_path', '').strip()
    if not vault_path or not Path(vault_path).exists():
        print(f"❌ vault_path does not exist: {vault_path}")
        print("   Check your config.json and make sure the path is correct.")
        sys.exit(1)

    print("=" * 60)
    print("  Blackboard Content Scraper")
    print("=" * 60)
    print(f"  Vault: {vault_path}")
    print()
    print("⚠️  Make sure Microsoft Edge is fully closed before continuing.")
    print("   Press Enter to start...")
    input()

    async with async_playwright() as p:
        print("🌐 Launching Edge with your existing session...")
        try:
            context = await p.chromium.launch_persistent_context(
                EDGE_USER_DATA,
                channel='msedge',
                headless=False,
                accept_downloads=True,
                args=['--no-first-run', '--no-default-browser-check'],
                ignore_default_args=['--enable-automation']
            )
        except Exception as e:
            print(f"❌ Could not launch Edge: {e}")
            print("   Make sure Edge is fully closed and try again.")
            sys.exit(1)

        page = context.pages[0] if context.pages else await context.new_page()

        print("📡 Loading your Blackboard module list...")
        modules = await get_modules(page)
        await page.close()

        if not modules:
            print("❌ No modules found on the Blackboard page.")
            print("   The page structure may have changed. Try opening Edge manually first.")
            await context.close()
            sys.exit(1)

        print(f"\n📋 Found {len(modules)} modules:")
        for i, m in enumerate(modules, 1):
            print(f"   {i:2}. {m['name']}")

        print(f"\n🚀 Starting download...\n")

        grand_total = 0
        for module in modules:
            count = await scrape_module(context, module['name'], module['url'], vault_path)
            grand_total += count

        await context.close()

    print("\n" + "=" * 60)
    print(f"  ✅  Done!  {grand_total} file(s) downloaded.")
    print(f"  📁  Saved to: {vault_path}")
    print()
    print("  💡  Open the AI extension and click ↺ to re-index your vault.")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
