#!/usr/bin/env python3
"""Собирает index.html из docs/spec.md компилятора SC.

    python3 gen.py ../sviroxk-compiler/docs/spec.md > index.html

Текст и примеры берутся только из спецификации: каждый её пример проверяет
tests/spec-examples.sh в репозитории компилятора, поэтому всё, что показывает
сайт, компилируется и печатает указанный вывод. Только стандартная библиотека
Python, без зависимостей.
"""
import html
import re
import subprocess
import sys
from pathlib import Path

COMPILER_URL = "https://github.com/sviroxk/sviroxk-compiler"

BLOCK_TITLES = {
    "sc": "Программа",
    "stdin": "Ввод",
    "sc-error": "Не компилируется",
}


def inline(text):
    """`код`, **жирный**, [текст](ссылка); остальное экранируется."""
    out = []
    for i, part in enumerate(re.split(r"(`[^`]*`)", text)):
        if i % 2:
            out.append("<code>" + html.escape(part[1:-1]) + "</code>")
            continue
        part = html.escape(part, quote=False)
        part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", part)
        part = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', part)
        out.append(part)
    return "".join(out)


def slug(title, used):
    m = re.match(r"(\d+)\.", title)
    base = "s" + m.group(1) if m else "s" + str(len(used) + 1)
    used.add(base)
    return base


def table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], cells[2:]
    out = ["<table><thead><tr>"]
    out += ["<th>" + inline(c) + "</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join("<td>" + inline(c) + "</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def convert(spec):
    """Возвращает (оглавление, html разделов). Вступление до первого ## не берётся:
    оно описывает формат блоков для тестов, на сайте его заменяют подписи."""
    lines = spec.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## "))
    lines = lines[start:]
    nav, out, used = [], [], set()
    para, items, rows = [], [], []
    prev_block = None
    open_section = False

    def flush():
        nonlocal para, items, rows
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
        if items:
            out.append("<ul>" + "".join("<li>" + inline(i) + "</li>" for i in items) + "</ul>")
        if rows:
            out.append(table(rows))
        para, items, rows = [], [], []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush()
            lang = line[3:].strip()
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            code = "\n".join(lines[i + 1:j])
            if lang == "text":
                title = "Ошибка (часть сообщения)" if prev_block == "sc-error" else "Вывод"
            else:
                title = BLOCK_TITLES.get(lang, "")
            cls = ' class="example-' + lang + '"' if lang else ""
            if title:
                out.append('<p class="label">' + title + "</p>")
            out.append("<pre" + cls + "><code>" + html.escape(code) + "</code></pre>")
            if lang != "stdin":
                prev_block = lang
            i = j + 1
            continue
        if line.startswith("## "):
            flush()
            if open_section:
                out.append("</section>")
            title = line[3:].strip()
            sid = slug(title, used)
            nav.append('<a href="#' + sid + '">' + inline(title) + "</a>")
            out.append('<section id="' + sid + '">\n<h2>' + inline(title) + "</h2>")
            open_section = True
        elif line.startswith("### "):
            flush()
            out.append("<h3>" + inline(line[4:].strip()) + "</h3>")
        elif line.startswith("|"):
            if para or items:
                flush()
            rows.append(line)
        elif line.startswith("- "):
            if para or rows:
                flush()
            items.append(line[2:].strip())
        elif line.startswith("  ") and items and line.strip():
            items[-1] += " " + line.strip()
        elif not line.strip():
            flush()
        else:
            if items or rows:
                flush()
            para.append(line.strip())
        i += 1
    flush()
    if open_section:
        out.append("</section>")
    return "\n".join(nav), "\n".join(out)


def source_commit(spec_path):
    try:
        return subprocess.run(
            ["git", "-C", str(Path(spec_path).resolve().parent), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


PAGE = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Документация языка программирования SC: типы, операторы, функции, структуры, массивы, примеры и ограничения текущего компилятора.">
  <meta name="theme-color" content="#111827">
  <title>SC — документация</title>
  <style>
{style}
  </style>
</head>
<body>
<!-- Файл создан gen.py из docs/spec.md компилятора{commit_note}. Не править руками. -->
<div class="layout">
  <aside>
    <strong>SC <span style="color:var(--muted);font-weight:400">/ Документация</span></strong>
    <nav aria-label="Разделы документации">
<a href="#about">О проекте</a><a href="#build">Сборка</a>
{nav}
    </nav>
  </aside>
  <main>
    <header id="about">
      <span class="badge">Экспериментальный компилятор · версия 0.3.0</span>
      <h1>SC</h1>
      <p>Язык SC и его компилятор: C++ и LLVM, на выходе LLVM IR. Эта страница собрана из спецификации языка (<code>docs/spec.md</code>). Каждый пример на ней компилируется и запускается тестами компилятора, и его вывод сверяется с блоком «Вывод».</p>
      <p><a href="{url}">Исходный код компилятора на GitHub ↗</a> · <a href="{url}/blob/main/docs/spec.md">спецификация</a></p>
      <p class="note">SC пока прототип. Что ещё не сделано — в разделе «Известные ограничения».</p>
    </header>
    <section id="build">
      <h2>Сборка</h2>
      <p>Нужен C++ компилятор и LLVM 18 (<code>llvm-config</code>). В клонированном репозитории:</p>
      <pre><code>./build.sh
./test.sh
timeout 10 ./sc hello.svx &gt; hello.ll &amp;&amp; lli hello.ll</code></pre>
    </section>
{body}
    <footer>SC documentation · страница собрана из <a href="{url}/blob/main/docs/spec.md">docs/spec.md</a>{commit_footer} · <a href="{url}">репозиторий компилятора</a></footer>
  </main>
</div>
</body>
</html>
"""

STYLE = """\
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--text:#e5e7eb;--muted:#a9b4c8;--accent:#64d8cb;--line:#26334d;--code:#080d18}
    *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}
    a{color:var(--accent)}a:hover{text-decoration:none}.layout{display:grid;grid-template-columns:260px minmax(0,820px);gap:48px;max-width:1200px;margin:auto;padding:36px 28px}
    aside{position:sticky;top:24px;align-self:start;max-height:calc(100vh - 48px);overflow:auto;border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:22px}
    aside strong{font-size:1.25rem;color:white}nav{display:grid;gap:5px;margin-top:18px}nav a{padding:5px 8px;border-radius:7px;text-decoration:none;color:var(--muted)}nav a:hover{background:#1c2942;color:white}
    main{min-width:0}header{padding:26px 0 34px;border-bottom:1px solid var(--line)}.badge{display:inline-block;border:1px solid #376d70;color:var(--accent);border-radius:999px;padding:3px 11px;font-size:.85rem}
    h1{font-size:clamp(2.4rem,7vw,4.6rem);line-height:1.05;letter-spacing:-.045em;margin:20px 0 14px}h2{margin-top:54px;padding-top:15px;border-top:1px solid var(--line);font-size:1.65rem}h3{margin-top:28px;color:#f3f4f6}p,li{color:var(--muted)}strong{color:var(--text)}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#b7f7dc;background:#172238;padding:2px 5px;border-radius:5px}
    pre{overflow:auto;background:var(--code);border:1px solid var(--line);border-radius:12px;padding:18px 20px;line-height:1.55}pre code{padding:0;background:none;color:#dbeafe}.note{border-left:3px solid var(--accent);background:var(--panel);padding:13px 17px;border-radius:0 9px 9px 0;color:var(--muted)}
    table{width:100%;border-collapse:collapse;display:block;overflow-x:auto}th,td{text-align:left;border-bottom:1px solid var(--line);padding:9px 12px}th{color:white}td{color:var(--muted)}.top{float:right;font-size:.9rem}
    footer{margin-top:60px;padding:22px 0;border-top:1px solid var(--line);color:var(--muted);font-size:.9rem}
    @media(max-width:850px){.layout{display:block;padding:16px}.layout aside{position:static;max-height:none;margin-bottom:28px}nav{grid-template-columns:repeat(2,minmax(0,1fr))}header{padding-top:18px}}
"""

STYLE_EXTRA = (
    ".label{margin:18px 0 -8px;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}"
    "pre.example-text code{color:#d1fae5}pre.example-sc-error{border-color:#7f1d1d}pre.example-stdin code{color:#fde68a}"
)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: gen.py path/to/docs/spec.md > index.html")
    spec_path = sys.argv[1]
    nav, body = convert(Path(spec_path).read_text(encoding="utf-8"))
    style = STYLE + "    " + STYLE_EXTRA
    commit = source_commit(spec_path)
    sys.stdout.write(PAGE.format(
        style=style, nav=nav, body=body, url=COMPILER_URL,
        commit_note=" (коммит " + commit + ")" if commit else "",
        commit_footer=" (коммит <code>" + commit + "</code>)" if commit else ""))


if __name__ == "__main__":
    main()
