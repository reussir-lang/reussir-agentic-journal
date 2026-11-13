"""Markdown to Forester markup conversion.

Used once for the initial migration of the in-tree Reussir design notes and
changelog, and kept so that a markdown draft can still be turned into a tree:

    python3 scripts/md2tree.py draft.md design-my-topic > trees/design/design-my-topic.tree

The output is a starting point: add the frontmatter (\\taxon, \\date, \\author,
...) by hand as described in AGENTS.md.
"""

from __future__ import annotations

import re
import sys

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

REPO_URL = "https://github.com/reussir-lang/reussir"

# Characters that are tokens of their own in Forester's lexer and are emitted
# through a verbatim span when they occur in prose.
_ALWAYS_VERB = set("\\{}[]#")
_HERALDS = ["~", "!!", "@@@", "<<>>", "~!~!~", "@~@~@~@"]


def slugify(text: str, limit: int = 48) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(s) > limit:
        s = s[:limit].rsplit("-", 1)[0]
    return s or "section"


def verb(body: str) -> str:
    """A verbatim span whose terminator does not occur in the body."""
    for h in _HERALDS:
        if (body + h).find(h) == len(body):
            return f"\\verb{h}|{body}{h}"
    raise ValueError("no usable verbatim herald for: " + body[:40])


def plain(node: SyntaxTreeNode) -> str:
    if node.type in ("text", "code_inline"):
        return node.content
    if node.type in ("softbreak", "hardbreak"):
        return " "
    return "".join(plain(c) for c in node.children)


class Converter:
    def __init__(self, address: str, link_map=None):
        self.address = address
        # Maps a markdown link target to a tree address or URL; returns None
        # to keep the target unchanged.
        self.link_map = link_map or (lambda href: None)
        self.used = set()
        self.sections = []  # (address, title) in document order

    # ---- inline -------------------------------------------------------

    def _unmatched_parens(self, nodes):
        """Positions of parentheses that have no partner among sibling text."""
        stack, bad = [], set()
        for i, n in enumerate(nodes):
            if n.type != "text":
                continue
            for j, ch in enumerate(n.content):
                if ch == "(":
                    stack.append((i, j))
                elif ch == ")":
                    if stack:
                        stack.pop()
                    else:
                        bad.add((i, j))
        bad.update(stack)
        return bad

    def _text(self, s: str, idx: int, bad) -> str:
        s = re.sub(r"\s*\n\s*", " ", s)
        out, run = [], []

        def flush():
            if run:
                out.append(verb("".join(run)))
                run.clear()

        for j, ch in enumerate(s):
            if ch in _ALWAYS_VERB or (ch in "()" and (idx, j) in bad):
                run.append(ch)
                continue
            flush()
            out.append("\\%" if ch == "%" else ch)
        flush()
        return "".join(out)

    def _pr_links(self, s: str, idx: int, bad) -> str:
        """Prose text, with `#123` and `owner/repo#123` turned into links."""
        out, pos = [], 0
        for m in re.finditer(r"(?:reussir-lang/reussir)?#(\d+)\b", s):
            out.append(self._text(s[pos:m.start()], idx, set()))
            out.append(f"\\pr{{{m.group(1)}}}")
            pos = m.end()
        if pos == 0:
            return self._text(s, idx, bad)
        out.append(self._text(s[pos:], idx, set()))
        return "".join(out)

    def inline(self, nodes) -> str:
        bad = self._unmatched_parens(nodes)
        out = []
        for i, n in enumerate(nodes):
            t = n.type
            if t == "text":
                out.append(self._pr_links(n.content, i, bad))
            elif t in ("softbreak", "hardbreak"):
                out.append(" ")
            elif t == "code_inline":
                m = re.fullmatch(r"(?:docs/design|crates/reussir-core/docs)/([a-z0-9-]+)\.md", n.content)
                if m:
                    out.append(f"[design-{m.group(1)}](design-{m.group(1)})")
                else:
                    out.append("\\code{" + verb(n.content) + "}")
            elif t == "em":
                out.append("\\em{" + self.inline(n.children) + "}")
            elif t == "strong":
                out.append("\\strong{" + self.inline(n.children) + "}")
            elif t == "link":
                href = n.attrs.get("href", "")
                dest = self.link_map(href) or href
                out.append(self.link(self.inline(n.children), dest))
            elif t == "html_inline":
                out.append(verb(n.content))
            elif t == "s":
                out.append(self.inline(n.children))
            else:
                raise ValueError(f"unhandled inline node {t}")
        return "".join(out)

    @staticmethod
    def link(text: str, dest: str) -> str:
        if re.fullmatch(r"[A-Za-z0-9-]+", dest):
            return f"[{text}]({dest})"
        # URLs may contain characters that are significant to the lexer.
        return f"\\<html:a>[href]{{{verb(dest)}}}{{{text}}}"

    # ---- blocks -------------------------------------------------------

    def block(self, n: SyntaxTreeNode) -> str:
        t = n.type
        if t == "paragraph":
            return "\\p{" + self.inline(n.children[0].children) + "}"
        if t in ("fence", "code_block"):
            code = n.content.rstrip("\n")
            return "\\pre{" + verb("\n" + code + "\n") + "}"
        if t in ("bullet_list", "ordered_list"):
            tag = "ul" if t == "bullet_list" else "ol"
            items = "\n".join(self.list_item(c) for c in n.children)
            return f"\\{tag}{{\n{items}\n}}"
        if t == "blockquote":
            return "\\blockquote{\n" + self.blocks(n.children) + "\n}"
        if t == "table":
            rows = []
            for part in n.children:
                for tr in part.children:
                    cells = "".join(
                        "\\" + c.type + "{" + self.inline(c.children[0].children) + "}"
                        for c in tr.children
                    )
                    rows.append("\\tr{" + cells + "}")
            return "\\table{\n" + "\n".join(rows) + "\n}"
        if t == "hr":
            return ""
        if t == "html_block":
            return "\\pre{" + verb("\n" + n.content.rstrip("\n") + "\n") + "}"
        raise ValueError(f"unhandled block node {t}")

    def list_item(self, n: SyntaxTreeNode) -> str:
        parts = []
        for c in n.children:
            if c.type == "paragraph" and len(n.children) == 1:
                parts.append(self.inline(c.children[0].children))
            else:
                parts.append(self.block(c))
        return "\\li{" + "\n".join(parts) + "}"

    def blocks(self, nodes) -> str:
        return "\n\n".join(b for b in (self.block(n) for n in nodes) if b)

    # ---- sections -----------------------------------------------------

    def _section_address(self, title_text: str) -> str:
        # A numbered heading ("2.2 Structural rules") keeps its number as the
        # address, so that "§2.2" in older references maps to "-s2-2".
        m = re.match(r"§?(\d+(?:\.\d+)*)[.:]?\s", title_text)
        if m:
            base = f"{self.address}-s{m.group(1).replace('.', '-')}"
        else:
            base = f"{self.address}-{slugify(title_text)}"
        addr, k = base, 2
        while addr in self.used:
            addr, k = f"{base}-{k}", k + 1
        self.used.add(addr)
        return addr

    def sections_from(self, nodes, level: int) -> str:
        """Blocks up to the first heading, then one subtree per heading."""
        out, i = [], 0
        lead = []
        while i < len(nodes) and nodes[i].type != "heading":
            lead.append(nodes[i])
            i += 1
        if lead:
            out.append(self.blocks(lead))
        while i < len(nodes):
            head = nodes[i]
            depth = int(head.tag[1])
            j = i + 1
            while j < len(nodes) and not (
                nodes[j].type == "heading" and int(nodes[j].tag[1]) <= depth
            ):
                j += 1
            title = self.inline(head.children[0].children)
            addr = self._section_address(plain(head))
            self.sections.append((addr, plain(head)))
            body = self.sections_from(nodes[i + 1 : j], depth + 1)
            out.append(f"\\subtree[{addr}]{{\n\\title{{{title}}}\n\n{body}\n}}")
            i = j
        return "\n\n".join(o for o in out if o)


def parse(md: str) -> SyntaxTreeNode:
    return SyntaxTreeNode(MarkdownIt("commonmark").enable("table").parse(md))


def convert_document(md: str, address: str, link_map=None):
    """Returns (title markup, plain title, body markup, converter)."""
    root = parse(md)
    nodes = list(root.children)
    conv = Converter(address, link_map)
    title, title_plain = "", ""
    if nodes and nodes[0].type == "heading" and nodes[0].tag == "h1":
        title = conv.inline(nodes[0].children[0].children)
        title_plain = plain(nodes[0])
        nodes = nodes[1:]
    body = conv.sections_from(nodes, 2)
    return title, title_plain, body, conv


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: md2tree.py <file.md> <tree-address>")
    title, _, body, _ = convert_document(open(sys.argv[1]).read(), sys.argv[2])
    print(f"\\title{{{title}}}\n\\import{{base-macros}}\n\n{body}")
