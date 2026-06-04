#!/usr/bin/env python3
"""Fetch Oracle NetSuite SDF XML reference pages and generate local examples."""

from __future__ import annotations

import html
import re
import sys
import textwrap
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


BASE_URL = "https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/"
SEED_URLS = [
    BASE_URL + "SDFxml.html",
    BASE_URL + "section_158492224846.html",
    BASE_URL + "section_158492241142.html",
    BASE_URL + "section_1516037866.html",
    BASE_URL + "section_159542604516.html",
    BASE_URL + "section_1516037901.html",
    BASE_URL + "section_158492209268.html",
]

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs" / "oracle-netsuite-sdf"
EXAMPLES_DIR = ROOT / "examples" / "sdf-objects"


@dataclass
class PageText:
    title: str = ""
    headings: list[str] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    section_links: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    tables: dict[str, list[list[str]]] = field(default_factory=dict)
    code_blocks: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)


class OracleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page = PageText()
        self._capture_title = False
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []
        self._link_href: str | None = None
        self._link_text: list[str] = []
        self._current_section = ""
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._pre_depth = 0
        self._pre_text: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"script", "style", "nav"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._capture_title = True
        elif tag in {"h1", "h2", "h3"}:
            self._heading_tag = tag
            self._heading_text = []
        elif tag == "a":
            self._link_href = attrs_dict.get("href")
            self._link_text = []
        elif tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag == "pre":
            self._pre_depth += 1
            self._pre_text = []
        elif tag in {"p", "li", "tr", "br"}:
            self.page.lines.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "nav"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag == "title":
            self._capture_title = False
        elif tag == self._heading_tag:
            text = normalize("".join(self._heading_text))
            if text:
                self.page.headings.append(text)
                if self._heading_tag == "h2":
                    self._current_section = text
            self._heading_tag = None
        elif tag == "a" and self._link_href:
            text = normalize("".join(self._link_text))
            if text:
                self.page.links.append((text, self._link_href))
                self.page.section_links.setdefault(self._current_section, []).append((text, self._link_href))
            self._link_href = None
            self._link_text = []
        elif tag in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(normalize("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.page.tables.setdefault(self._current_section, []).append(self._row)
            self._row = None
        elif tag == "pre" and self._pre_depth:
            block = html.unescape("".join(self._pre_text)).strip()
            if block:
                self.page.code_blocks.append(block)
            self._pre_depth -= 1
            self._pre_text = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._capture_title:
            self.page.title += data
        if self._heading_tag:
            self._heading_text.append(data)
        if self._link_href is not None:
            self._link_text.append(data)
        if self._cell is not None:
            self._cell.append(data)
        if self._pre_depth:
            self._pre_text.append(data)
        self.page.lines.append(data)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "cataloge-ns-sdf-doc-fetcher/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_page(url: str) -> PageText:
    parser = OracleParser()
    parser.feed(fetch(url))
    parser.page.title = normalize(parser.page.title.replace("NetSuite Applications Suite - ", ""))
    parser.page.lines = [normalize(line) for line in "".join(parser.page.lines).splitlines()]
    parser.page.lines = [line for line in parser.page.lines if line]
    return parser.page


def absolute_url(href: str) -> str:
    return urllib.parse.urljoin(BASE_URL, href)


def object_links(page: PageText) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    for text, href in page.links:
        if text in {"Next", "Previous"}:
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", text) and href.startswith("SDFxml_"):
            links.append((text, absolute_url(href)))
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for name, url in links:
        if name not in seen:
            seen.add(name)
            result.append((name, url))
    return result


def field_names(page: PageText, section_name: str) -> list[str]:
    names: list[str] = []
    for row in page.tables.get(section_name, []):
        if not row or row[0] == "Name":
            continue
        name = row[0]
        if re.fullmatch(r"[a-z][a-z0-9_]*", name):
            names.append(name)
    return dedupe(names)


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def object_summary(name: str, url: str, page: PageText) -> dict[str, object]:
    return {
        "name": name,
        "title": page.headings[0] if page.headings else name,
        "url": url,
        "features": feature_dependencies(page),
        "attributes": field_names(page, "Attributes"),
        "fields": field_names(page, "Fields"),
        "structured_fields": [
            text
            for text, href in page.section_links.get("Structured Fields", [])
            if href.startswith("SDFxml_") and text.islower()
        ],
    }


def feature_dependencies(page: PageText) -> list[str]:
    try:
        start = page.lines.index("Feature Dependencies")
    except ValueError:
        return []
    features: list[str] = []
    for line in page.lines[start + 1 :]:
        if line in {"Attributes", "Fields", "Structured Fields"}:
            break
        if re.fullmatch(r"[A-Z0-9_]+", line):
            features.append(line)
    return features


def xml_value(field: str) -> str:
    if field.startswith("is") or field.startswith("show") or field.startswith("all"):
        return "F"
    if field in {"label", "name", "title", "description", "linklabel"}:
        return f"Example {field}"
    if field.endswith("role"):
        return "[scriptid=customrole_example]"
    if field in {"center", "centertab"}:
        return f"[scriptid=cust{field}_example]"
    if field.endswith("scriptfile") or field == "scriptfile":
        return "[src=FileCabinet/SuiteScripts/example.js]"
    return f"TODO_{field}"


def render_example(summary: dict[str, object]) -> str:
    name = str(summary["name"])
    attrs = summary["attributes"]
    scriptid = f"cust{name}_example"
    if name.endswith("script"):
        scriptid = f"customscript_{name}_example"
    elif name.endswith("customfield"):
        scriptid = f"custrecord_{name}_example"
    attr_text = f' scriptid="{scriptid}"' if "scriptid" in attrs else ""

    lines = [f"<{name}{attr_text}>"]
    for field in list(summary["fields"])[:20]:
        if field == "scriptid":
            continue
        lines.append(f"  <{field}>{xml_value(field)}</{field}>")
    lines.append(f"</{name}>")
    return "\n".join(lines) + "\n"


def extract_topic_examples(seed_pages: dict[str, PageText]) -> list[tuple[str, str, str]]:
    examples: list[tuple[str, str, str]] = []
    for url, page in seed_pages.items():
        for block in page.code_blocks:
            if block.startswith("<") and block.endswith(">"):
                title = page.headings[0] if page.headings else page.title
                examples.append((title, url, block))
    return examples


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    seed_pages = {url: parse_page(url) for url in SEED_URLS}
    objects = object_links(seed_pages[SEED_URLS[0]])
    summaries = []
    for name, url in objects:
        page = parse_page(url)
        summary = object_summary(name, url, page)
        summaries.append(summary)
        (EXAMPLES_DIR / f"{name}.xml").write_text(render_example(summary), encoding="utf-8")

    examples = extract_topic_examples(seed_pages)
    topic_examples_md = ["# Oracle Topic Examples", ""]
    for title, url, block in examples:
        topic_examples_md.extend(
            [
                f"## {title}",
                "",
                f"Source: {url}",
                "",
                "```xml",
                textwrap.dedent(block).strip(),
                "```",
                "",
            ]
        )
    (DOCS_DIR / "topic-examples.md").write_text("\n".join(topic_examples_md), encoding="utf-8")

    index = [
        "# NetSuite SDF XML Object Definitions",
        "",
        "Generated from Oracle NetSuite Online Help pages.",
        "",
        "Seed URLs:",
        *[f"- {url}" for url in SEED_URLS],
        "",
        "## Objects",
        "",
        "| Object | Source | Features | Attributes | Fields | Structured fields | Example |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for summary in summaries:
        name = str(summary["name"])
        features = ", ".join(summary["features"]) or "-"
        attrs = ", ".join(summary["attributes"]) or "-"
        fields = ", ".join(summary["fields"]) or "-"
        structured = ", ".join(dedupe(list(summary["structured_fields"]))) or "-"
        index.append(
            f"| `{name}` | [Oracle]({summary['url']}) | {features} | {attrs} | {fields} | {structured} | "
            f"[XML](../../examples/sdf-objects/{name}.xml) |"
        )
    (DOCS_DIR / "object-definitions.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    print(f"Wrote {len(summaries)} object examples to {EXAMPLES_DIR}")
    print(f"Wrote {DOCS_DIR / 'object-definitions.md'}")
    print(f"Wrote {DOCS_DIR / 'topic-examples.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
