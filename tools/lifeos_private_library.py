#!/usr/bin/env python3
"""Build a local-only full-text reader from user-provided source files.

This tool never fetches copyrighted material. Put files you already have rights to
read under ``private/library/`` (ignored by git), then run:

    python tools/lifeos_private_library.py build

Supported inputs: .txt, .md, .markdown, .html, .htm. Output is written to the
private local vault at ``output/private-readings/`` and is intentionally excluded
from the Vercel public build.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from lifeos_paths import APP_ROOT, VAULT_ROOT

SOURCE_ROOT = Path(os.environ.get("LIFEOS_PRIVATE_LIBRARY", APP_ROOT / "private" / "library")).expanduser()
OUT = VAULT_ROOT / "output" / "private-readings"
SUPPORTED = {".txt", ".md", ".markdown", ".html", ".htm"}

BASE_CSS = """
*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#f7f5f0;color:#151719;font-family:Inter,system-ui,-apple-system,sans-serif}
a{color:inherit}.wrap{width:min(820px,calc(100% - 32px));margin:0 auto;padding:18px 0 64px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center;border-bottom:1px solid #d8d3c8;padding-bottom:12px;color:#676b66;font:800 13px/1 system-ui;flex-wrap:wrap}.top a{text-decoration:none}.kicker{font:850 12px/1 system-ui;letter-spacing:.12em;text-transform:uppercase;color:#77736a;margin:26px 0 8px}h1{font:850 clamp(36px,7vw,68px)/.95 Georgia,serif;margin:0 0 10px}.meta{color:#5f665f;font:750 13px/1.45 system-ui;margin:0 0 26px}.reader{font:500 19px/1.72 Georgia,serif}.reader h1,.reader h2,.reader h3{font-family:Georgia,serif;line-height:1.08;margin:34px 0 10px}.reader h1{font-size:40px}.reader h2{font-size:31px}.reader h3{font-size:24px}.reader p{margin:0 0 17px}.reader ul,.reader ol{padding-left:24px}.reader li{margin:8px 0}.reader blockquote{border-left:3px solid #151719;margin:20px 0;padding:2px 0 2px 16px;color:#39413c}.reader img{max-width:100%;height:auto;border:1px solid #d8d3c8}.sourceframe{width:100%;min-height:80vh;border:1px solid #d8d3c8;background:white}.hlbar{position:fixed;z-index:99;display:none;gap:6px;background:#151719;color:#fff;border:1px solid #000;border-radius:999px;padding:6px;box-shadow:0 10px 30px rgba(0,0,0,.22)}.hlbar.show{display:flex}.hlbar button{border:0;border-radius:999px;background:#fff;color:#151719;font:850 13px/1 system-ui;padding:9px 12px;cursor:pointer}.hlbar [data-hl-clear]{background:#2b2b2b;color:#fff}.user-highlight{background:#ffe66d;color:#151719;border-radius:3px;padding:0 .08em;box-decoration-break:clone;-webkit-box-decoration-break:clone}.index{display:grid;gap:10px;margin-top:24px}.card{display:block;text-decoration:none;color:#151719;background:#fff;border:1px solid #d8d3c8;padding:16px}.card span{display:block;color:#77736a;font:850 11px/1 system-ui;letter-spacing:.1em;text-transform:uppercase}.card strong{display:block;font:850 25px/1.1 Georgia,serif;margin:7px 0}.card em{font:650 13px/1.4 system-ui;color:#5f665f;font-style:normal}.empty{background:#fff;border:1px solid #d8d3c8;padding:18px;margin-top:24px;color:#5f665f;line-height:1.55}
"""

HIGHLIGHT_JS = r"""
(function(){
const root=document.querySelector('[data-highlight-root]');
const id=document.body.dataset.readingId||location.pathname;
if(!root)return;
const key='lifeos.private.highlights.v1.'+id;
const bar=document.createElement('div');
bar.className='hlbar';
bar.innerHTML='<button type="button" data-hl-add>Highlight</button><button type="button" data-hl-clear>Clear</button>';
document.body.appendChild(bar);
let savedRange=null;
function hide(){bar.classList.remove('show')}
function usableSelection(){const sel=window.getSelection();if(!sel||sel.isCollapsed||sel.rangeCount===0)return null;const range=sel.getRangeAt(0);if(!root.contains(range.commonAncestorContainer))return null;if(String(sel).trim().length<2)return null;return range}
function place(){const range=usableSelection();if(!range){hide();return}savedRange=range.cloneRange();const rect=range.getBoundingClientRect();bar.style.left=Math.max(10,Math.min(window.innerWidth-170,rect.left+rect.width/2-70))+'px';bar.style.top=Math.max(10,rect.top-46)+'px';bar.classList.add('show')}
function skipNode(n){const p=n.parentElement;return !p||p.closest('mark.user-highlight,button,a,script,style,.hlbar')}
function textNodes(){const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){return skipNode(n)?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT}});const out=[];let n;while((n=walker.nextNode()))out.push(n);return out}
function unwrap(mark){const parent=mark.parentNode;while(mark.firstChild)parent.insertBefore(mark.firstChild,mark);parent.removeChild(mark);parent.normalize()}
function save(){const items=[...root.querySelectorAll('mark.user-highlight')].map(m=>m.textContent.trim()).filter(Boolean).slice(0,500);localStorage.setItem(key,JSON.stringify(items))}
function highlightRange(range){const mark=document.createElement('mark');mark.className='user-highlight';mark.appendChild(range.extractContents());range.insertNode(mark);mark.normalize();save()}
function restoreOne(text){for(const n of textNodes()){const i=n.nodeValue.indexOf(text);if(i<0)continue;const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+text.length);highlightRange(r);return}}
function restore(){let items=[];try{items=JSON.parse(localStorage.getItem(key)||'[]')}catch{}if(Array.isArray(items))items.forEach(restoreOne)}
bar.querySelector('[data-hl-add]').addEventListener('click',()=>{if(!savedRange)return hide();try{highlightRange(savedRange)}catch(e){}window.getSelection()?.removeAllRanges();hide()});
bar.querySelector('[data-hl-clear]').addEventListener('click',()=>{root.querySelectorAll('mark.user-highlight').forEach(unwrap);localStorage.removeItem(key);window.getSelection()?.removeAllRanges();hide()});
root.addEventListener('mouseup',()=>setTimeout(place,0));root.addEventListener('touchend',()=>setTimeout(place,80),{passive:true});document.addEventListener('selectionchange',()=>{if(!usableSelection())hide()});window.addEventListener('scroll',hide,{passive:true});restore();
})();
"""


def slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return value[:90] or hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def discover() -> list[Path]:
    if not SOURCE_ROOT.exists():
        return []
    return sorted(p for p in SOURCE_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def title_for(path: Path, text: str) -> str:
    yaml = re.search(r"^---\s*\n(.*?)\n---", text, re.S)
    if yaml:
        m = re.search(r"^title:\s*(.+)$", yaml.group(1), re.M)
        if m:
            return m.group(1).strip().strip('"\'')
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    if path.suffix.lower() in {".html", ".htm"}:
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
        if m:
            return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first[:100] if first else path.stem.replace("-", " ").replace("_", " ").title()


def markdown_to_html(text: str) -> str:
    out: list[str] = []
    in_ul = False
    paras: list[str] = []

    def inline(value: str) -> str:
        value = html.escape(value)
        value = re.sub(r"!\[([^\]]*)\]\((https?://[^)]+)\)", r"<img alt=\"\1\" src=\"\2\">", value)
        value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"<a href=\"\2\" target=\"_blank\" rel=\"noopener\">\1</a>", value)
        value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
        value = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", value)
        return value

    def flush_para() -> None:
        nonlocal paras
        if paras:
            out.append("<p>" + inline(" ".join(paras)) + "</p>")
            paras = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para(); close_ul(); continue
        h = re.match(r"^(#{1,3})\s+(.+)$", line)
        if h:
            flush_para(); close_ul()
            level = len(h.group(1))
            out.append(f"<h{level}>{inline(h.group(2).strip())}</h{level}>")
            continue
        li = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if li:
            flush_para()
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(li.group(1).strip())}</li>")
            continue
        if line.startswith(">"):
            flush_para(); close_ul()
            out.append(f"<blockquote>{inline(line.lstrip('> ').strip())}</blockquote>")
            continue
        paras.append(line.strip())
    flush_para(); close_ul()
    return "\n".join(out)


def render_content(path: Path, text: str) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return f"<iframe class='sourceframe' sandbox srcdoc='{html.escape(text, quote=True)}'></iframe>"
    return markdown_to_html(text)


def reading_record(path: Path) -> dict[str, Any]:
    text = read_text(path)
    rel = path.relative_to(SOURCE_ROOT)
    title = title_for(path, text)
    item_id = slug(str(rel.with_suffix("")))
    categories = [part.lower() for part in rel.parts[:-1]] or ["private"]
    words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", text)))
    return {
        "id": item_id,
        "title": title,
        "relative_path": rel.as_posix(),
        "categories": categories,
        "words": words,
        "minutes": max(1, round(words / 220)),
        "source_path": str(path),
        "content_html": render_content(path, text),
    }


def render_reading(item: dict[str, Any]) -> str:
    cats = ", ".join(item["categories"])
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(item['title'])}</title><style>{BASE_CSS}</style></head><body data-reading-id='{html.escape(item['id'])}'><div class='wrap'><div class='top'><a href='/private'>← Private library</a><span>local-only</span></div><div class='kicker'>{html.escape(cats)}</div><h1>{html.escape(item['title'])}</h1><p class='meta'>{item['words']:,} words · about {item['minutes']} min · {html.escape(item['relative_path'])}</p><main class='reader' data-highlight-root>{item['content_html']}</main></div><script>{HIGHLIGHT_JS}</script></body></html>"""


def render_index(items: list[dict[str, Any]]) -> str:
    if items:
        cards = "\n".join(
            f"<a class='card' href='/output/private-readings/{html.escape(item['id'])}.html'><span>{html.escape(', '.join(item['categories']))} · {item['minutes']} min</span><strong>{html.escape(item['title'])}</strong><em>{html.escape(item['relative_path'])}</em></a>"
            for item in items
        )
    else:
        cards = "<div class='empty'><strong>No private readings yet.</strong><p>Put .txt, .md, or .html files under <code>private/library/</code>, then run <code>python tools/lifeos_private_library.py build</code>. The <code>private/</code> folder is git-ignored and not deployed to Vercel.</p></div>"
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>LifeOS Private Library</title><style>{BASE_CSS}</style></head><body><div class='wrap'><div class='top'><a href='/learn'>← Learn</a><span>local-only private reader</span></div><div class='kicker'>Private Library</div><h1>Full-text local readings</h1><p class='meta'>User-provided files only. Nothing here is committed or deployed.</p><section class='index'>{cards}</section></div></body></html>"""


def init_library() -> dict[str, Any]:
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    readme = SOURCE_ROOT / "README.md"
    if not readme.exists():
        readme.write_text(
            "# LifeOS private library\n\nPut personal-use `.txt`, `.md`, or `.html` readings here. This folder is ignored by git and is not deployed to Vercel.\n",
            encoding="utf-8",
        )
    return {"source_root": str(SOURCE_ROOT), "readme": str(readme)}


def build() -> dict[str, Any]:
    init_library()
    OUT.mkdir(parents=True, exist_ok=True)
    items = [reading_record(path) for path in discover() if path.name != "README.md"]
    for item in items:
        (OUT / f"{item['id']}.html").write_text(render_reading(item), encoding="utf-8")
    index = render_index(items)
    (OUT / "index.html").write_text(index, encoding="utf-8")
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_root": str(SOURCE_ROOT),
        "output": str(OUT),
        "count": len(items),
        "items": [{k: item[k] for k in ["id", "title", "relative_path", "categories", "words", "minutes"]} for item in items],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local-only LifeOS private reading pages")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="Create the ignored private/library folder")
    sub.add_parser("build", help="Build private full-text reading pages")
    sub.add_parser("list", help="List discovered private source files")
    args = parser.parse_args()
    if args.cmd == "init":
        print(json.dumps(init_library(), indent=2))
    elif args.cmd == "build":
        print(json.dumps(build(), indent=2))
    elif args.cmd == "list":
        print(json.dumps([str(p) for p in discover()], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
