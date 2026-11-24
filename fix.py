"""Rewrite the published daisyui.css the way the pull request changes input.css and select.css.

usage: python fix.py daisyui.css > daisyui-fix.css
"""

import re
import sys

COLOR = "color:color-mix(in oklab, var(--color-base-content) 40%, transparent)"
TYPES = ",".join(f"[type={t}]" for t in ("url", "tel", "email", "number"))


def block_end(css, start):
    """Index just past the brace that closes the block opening at or after ``start``."""
    depth = 0
    for i in range(css.index("{", start), len(css)):
        depth += {"{": 1, "}": -1}.get(css[i], 0)
        if depth == 0:
            return i + 1
    raise ValueError(start)


def flatten_rtl(css):
    pattern = r":is\(([^()]*?)\[type=url\],([^()]*?)\[type=tel\],([^()]*?)\[type=email\],([^()]*?)\[type=number\]\):dir\(rtl\)"
    repl = r"\1[type=url]:dir(rtl),\2[type=tel]:dir(rtl),\3[type=email]:dir(rtl),\4[type=number]:dir(rtl)"
    return re.subn(pattern, repl, css)


def flatten_disabled(css, tag):
    css, a = re.subn(re.escape(f"&:is({tag}),& :is({tag}){{{COLOR}}}"), f"&:is({tag}){{{COLOR}}}", css)
    flat = f"&:has(>{tag}[disabled]) {tag},&:is(:disabled,[disabled]) {tag},fieldset:disabled & {tag}{{{COLOR}}}"
    anchor = f"&:has(>{tag}[disabled])>{tag}[disabled]{{"
    css, b = re.subn(re.escape(anchor), lambda m: flat + m[0], css)
    return css, (a, b)


def flatten_ltr(css):
    nested = "&[type=url],&[type=tel],&[type=email],&[type=number]{direction:ltr}"
    flat = f"input&:is({TYPES}),& input:is({TYPES}){{direction:ltr}}"
    out, pos, n = [], 0, 0
    while (start := css.find("input&,& input{", pos)) != -1:
        end = block_end(css, start)
        body = css[start:end]
        if nested in body:
            body = body.replace(nested, "") + flat
            n += 1
        out += [css[pos:start], body]
        pos = end
    return "".join(out) + css[pos:], n


def main():
    css = open(sys.argv[1]).read()
    css, rtl = flatten_rtl(css)
    css, dis_input = flatten_disabled(css, "input")
    css, dis_select = flatten_disabled(css, "select")
    css, ltr = flatten_ltr(css)
    print(f"rtl {rtl}, disabled input {dis_input}, disabled select {dis_select}, ltr {ltr}", file=sys.stderr)
    sys.stdout.write(css)


if __name__ == "__main__":
    main()
