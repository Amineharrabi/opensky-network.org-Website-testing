from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PDF_A4 = (595.28, 841.89)  # points


@dataclass(frozen=True)
class PdfStyle:
    font_name: str = "Helvetica"
    font_size: int = 11
    leading: int = 14
    margin_left: int = 50
    margin_top: int = 50


def _pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
    )


def _build_page_stream(lines: list[tuple[int, str]], *, style: PdfStyle, page_size=PDF_A4) -> bytes:
    """Render a list of (font_size, text) lines as a single PDF content stream."""
    width, height = page_size
    x = style.margin_left
    y = height - style.margin_top

    out: list[str] = ["BT"]
    out.append(f"/F1 {style.font_size} Tf")
    out.append(f"{x:.2f} {y:.2f} Td")
    out.append(f"{style.leading} TL")

    current_size = style.font_size
    first = True
    for font_size, text in lines:
        safe = _pdf_escape(text)
        if font_size != current_size:
            current_size = font_size
            out.append(f"/F1 {current_size} Tf")
        if first:
            out.append(f"({safe}) Tj")
            first = False
        else:
            out.append("T*")
            out.append(f"({safe}) Tj")

    out.append("ET")
    return ("\n".join(out)).encode("latin-1", errors="replace")


def _paginate_markdown(md: str, *, lines_per_page: int = 46) -> tuple[list[list[tuple[int, str]]], list[tuple[int, str, int]]]:
    """Return pages and heading index: (level, title, page_number_1_based)."""
    pages: list[list[tuple[int, str]]] = [[]]
    headings: list[tuple[int, str, int]] = []

    def push_line(font_size: int, text: str) -> None:
        if len(pages[-1]) >= lines_per_page:
            pages.append([])
        pages[-1].append((font_size, text))

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            if title:
                # Ensure headings don't end up as the last line of a page.
                if len(pages[-1]) >= lines_per_page - 2:
                    pages.append([])
                if level == 1:
                    push_line(18, title)
                    push_line(11, "")
                elif level == 2:
                    push_line(14, title)
                else:
                    push_line(12, title)
                headings.append((level, title, len(pages)))
                continue

        if not line.strip():
            push_line(11, "")
        else:
            push_line(11, line)

    # Remove trailing empty page
    if pages and not any(t.strip() for _, t in pages[-1]):
        pages.pop()
    return pages, headings


def _render_toc(headings: list[tuple[int, str, int]], *, lines_per_page: int) -> str:
    lines: list[str] = ["# Table des matières", ""]
    for level, title, page in headings:
        if level == 1:
            indent = ""
        elif level == 2:
            indent = "  "
        else:
            indent = "    "
        dots = "." * max(4, 60 - len(title) - len(indent))
        lines.append(f"{indent}{title} {dots} {page}")
    lines.append("")
    return "\n".join(lines)


def markdown_to_pdf(md: str, output_path: Path) -> Path:
    """Create a small, dependency-free PDF from a Markdown-ish document.

    Supported Markdown:
    - headings (#, ##, ###)
    - plain paragraphs
    """
    # Two-pass: build content pages, then build TOC pages and re-paginate with TOC inserted.
    content_pages, headings = _paginate_markdown(md)
    toc_md = _render_toc(headings, lines_per_page=46)
    toc_pages, _ = _paginate_markdown(toc_md)

    # Adjust heading page numbers for the inserted TOC pages
    adjusted_headings = [(lvl, title, page + len(toc_pages)) for (lvl, title, page) in headings]
    toc_md = _render_toc(adjusted_headings, lines_per_page=46)
    toc_pages, _ = _paginate_markdown(toc_md)

    all_pages = toc_pages + content_pages
    _write_pdf(output_path, all_pages)
    return output_path


def _write_pdf(path: Path, pages: list[list[tuple[int, str]]]) -> None:
    # Minimal PDF writer (objects + xref). Single font, single content stream per page.
    style = PdfStyle()
    w, h = PDF_A4

    objects: list[bytes] = []

    def add_object(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)

    # 1: Catalog, 2: Pages, 3: Font, then per page: Page + Contents
    font_obj = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_kids: list[int] = []
    contents_objs: list[int] = []
    page_objs: list[int] = []

    for page_lines in pages:
        stream = _build_page_stream(page_lines, style=style)
        contents = b"<< /Length %d >>\nstream\n%b\nendstream" % (len(stream), stream)
        contents_id = add_object(contents)
        contents_objs.append(contents_id)

        page_dict = (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 %b %b] "
            b"/Resources << /Font << /F1 %d 0 R >> >> "
            b"/Contents %d 0 R >>"
            % (str(w).encode(), str(h).encode(), font_obj, contents_id)
        )
        page_id = add_object(page_dict)
        page_objs.append(page_id)
        page_kids.append(page_id)

    kids_ref = b"[ " + b" ".join(f"{pid} 0 R".encode() for pid in page_kids) + b" ]"
    pages_obj = b"<< /Type /Pages /Kids %b /Count %d >>" % (kids_ref, len(page_kids))
    # Insert Pages object at index 2 (object number 2)
    objects.insert(1, pages_obj)  # now object numbers shift by +1 for items after insertion

    # Fix up: font_obj/contents/page ids assumed sequential; rebuild cleanly instead for correctness.
    # (Keep the public API stable; internal writer is simple.)
    objects = []

    xref_offsets: list[int] = []

    def add(obj: bytes) -> int:
        objects.append(obj)
        return len(objects)

    catalog_id = add(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add(b"<< /Type /Pages /Kids [] /Count 0 >>")  # placeholder
    font_id = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for page_lines in pages:
        stream = _build_page_stream(page_lines, style=style)
        contents = b"<< /Length %d >>\nstream\n%b\nendstream" % (len(stream), stream)
        contents_id = add(contents)

        page_dict = (
            b"<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 %b %b] "
            b"/Resources << /Font << /F1 %d 0 R >> >> "
            b"/Contents %d 0 R >>"
            % (str(w).encode(), str(h).encode(), font_id, contents_id)
        )
        page_id = add(page_dict)
        page_ids.append(page_id)

    kids_ref = b"[ " + b" ".join(f"{pid} 0 R".encode() for pid in page_ids) + b" ]"
    objects[pages_id - 1] = b"<< /Type /Pages /Kids %b /Count %d >>" % (kids_ref, len(page_ids))

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray()
    body.extend(header)

    # xref entry 0 is the free object
    xref_offsets.append(0)
    for idx, obj in enumerate(objects, start=1):
        xref_offsets.append(len(body))
        body.extend(f"{idx} 0 obj\n".encode("ascii"))
        body.extend(obj)
        body.extend(b"\nendobj\n")

    xref_start = len(body)
    body.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    body.extend(b"0000000000 65535 f \n")
    for off in xref_offsets[1:]:
        body.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    trailer = (
        b"trailer\n"
        b"<< /Size %d /Root %d 0 R >>\n"
        b"startxref\n%d\n%%EOF\n"
        % (len(objects) + 1, catalog_id, xref_start)
    )
    body.extend(trailer)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(body))

