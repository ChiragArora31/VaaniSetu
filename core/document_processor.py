"""Document text extraction and best-effort translated exports."""

from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from core.file_utils import write_text
from config.settings import TESSDATA_DIR


class DocumentProcessingError(RuntimeError):
    """Raised when a document cannot be converted into translatable text."""


MAX_OFFICE_MEMBER_BYTES = 16 * 1024 * 1024
MAX_OFFICE_TOTAL_BYTES = 64 * 1024 * 1024
MAX_OFFICE_MEMBERS = 2_000


@dataclass(frozen=True)
class DocumentText:
    text: str
    kind: str
    warning: str | None = None


def extract_document_text(path: Path) -> DocumentText:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return DocumentText(_extract_office_xml(path, "word/document.xml"), "docx")
    if suffix == ".pptx":
        return DocumentText(_extract_pptx(path), "pptx")
    if suffix == ".xlsx":
        return DocumentText(_extract_xlsx(path), "xlsx")
    if suffix in {".csv", ".tsv"}:
        return DocumentText(_extract_delimited(path, "\t" if suffix == ".tsv" else ","), suffix.lstrip("."))
    raise DocumentProcessingError(f"Unsupported document extension: {suffix}")


def write_document_exports(source_path: Path, translated_text: str, output_dir: Path) -> dict[str, Path]:
    suffix = source_path.suffix.lower()
    artifacts = {
        "translated_txt": write_text(output_dir / "translated_text.txt", translated_text),
        "translated_markdown": write_text(
            output_dir / "translated_document.md",
            f"# Translated {source_path.name}\n\n{translated_text}\n",
        ),
    }
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        artifacts["translated_table"] = write_text(
            output_dir / f"translated_table{suffix}",
            _text_to_delimited(translated_text, delimiter),
        )
    return artifacts


def _extract_pdf(path: Path) -> DocumentText:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentProcessingError(
            "PDF extraction dependency is not installed. Install the document extras from requirements.txt."
        ) from exc

    try:
        reader = PdfReader(str(path))
        page_text = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise DocumentProcessingError("The PDF could not be read.") from exc

    text = _clean_lines("\n\n".join(page_text))
    if not text:
        text = _ocr_pdf(path)
        return DocumentText(
            text,
            "pdf-ocr",
            "This scanned PDF was read with automatic local OCR. Review names, numbers, and agricultural terms before reuse.",
        )
    return DocumentText(
        text,
        "pdf",
        "PDF export is text-preserving best effort; layout-perfect PDF reconstruction is outside the MVP path.",
    )


def _ocr_pdf(path: Path) -> str:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        raise DocumentProcessingError(
            "This PDF appears to be scanned or image-only, and automatic OCR is not ready on this worker."
        )
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise DocumentProcessingError(
            "This PDF appears to be scanned or image-only, and the local PDF renderer is not installed."
        ) from exc

    try:
        document = pdfium.PdfDocument(str(path))
    except Exception as exc:
        raise DocumentProcessingError("The scanned PDF could not be opened for OCR.") from exc

    pages: list[str] = []
    try:
        with tempfile.TemporaryDirectory(prefix="vaanisetu_ocr_") as directory:
            for index in range(len(document)):
                image_path = Path(directory) / f"page-{index + 1}.png"
                try:
                    bitmap = document[index].render(scale=2.2)
                    bitmap.to_pil().save(image_path)
                    command = [tesseract, str(image_path), "stdout"]
                    if all((TESSDATA_DIR / f"{language}.traineddata").exists() for language in ("eng", "hin", "mar")):
                        command.extend(["--tessdata-dir", str(TESSDATA_DIR)])
                    command.extend(["-l", "eng+hin+mar", "--psm", "6"])
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=120,
                    )
                except subprocess.TimeoutExpired as exc:
                    raise DocumentProcessingError(f"OCR timed out on page {index + 1}.") from exc
                except Exception as exc:
                    raise DocumentProcessingError(f"OCR could not render page {index + 1}.") from exc
                if result.returncode != 0:
                    raise DocumentProcessingError(result.stderr.strip() or f"OCR failed on page {index + 1}.")
                pages.append(result.stdout)
    finally:
        document.close()
    text = _clean_lines("\n\n".join(pages))
    if not text:
        raise DocumentProcessingError("No readable text was found in this scanned PDF.")
    return text


def _extract_office_xml(path: Path, member: str) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            _validate_office_archive(archive)
            data = _read_office_member(archive, member)
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError(f"The Office document could not be read: {path.name}") from exc
    return _xml_text(data)


def _extract_pptx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            _validate_office_archive(archive)
            slide_names = sorted(name for name in archive.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", name))
            slides = [_xml_text(_read_office_member(archive, name)) for name in slide_names]
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError("The PowerPoint file could not be read.") from exc
    return _clean_lines("\n\n".join(slide for slide in slides if slide))


def _extract_xlsx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            _validate_office_archive(archive)
            shared_strings = _shared_strings(archive)
            sheet_names = sorted(name for name in archive.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", name))
            rows = [_sheet_text(_read_office_member(archive, name), shared_strings) for name in sheet_names]
    except DocumentProcessingError:
        raise
    except Exception as exc:
        raise DocumentProcessingError("The Excel workbook could not be read.") from exc
    return _clean_lines("\n".join(row for row in rows if row))


def _extract_delimited(path: Path, delimiter: str) -> str:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle, delimiter=delimiter)
            rows = [" | ".join(cell.strip() for cell in row if cell.strip()) for row in reader]
    except UnicodeDecodeError as exc:
        raise DocumentProcessingError("CSV/TSV files must be UTF-8 encoded.") from exc
    return _clean_lines("\n".join(row for row in rows if row))


def _xml_text(data: bytes) -> str:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise DocumentProcessingError("Document XML is malformed.") from exc
    values = []
    for element in root.iter():
        if element.tag.endswith("}t") or element.tag.endswith("}instrText"):
            if element.text and element.text.strip():
                values.append(element.text.strip())
    return _clean_lines("\n".join(values))


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        data = _read_office_member(archive, "xl/sharedStrings.xml")
    except KeyError:
        return []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []
    values = []
    for item in root:
        parts = []
        for element in item.iter():
            if element.tag.endswith("}t") and element.text:
                parts.append(element.text)
        values.append("".join(parts).strip())
    return values


def _validate_office_archive(archive: zipfile.ZipFile) -> None:
    infos = archive.infolist()
    if len(infos) > MAX_OFFICE_MEMBERS:
        raise DocumentProcessingError("The Office document contains too many files to process safely.")
    if sum(info.file_size for info in infos) > MAX_OFFICE_TOTAL_BYTES:
        raise DocumentProcessingError("The Office document expands beyond the safe processing limit.")
    names: set[str] = set()
    for info in infos:
        folded = info.filename.casefold()
        if folded in names:
            raise DocumentProcessingError(f"The Office document contains a duplicate file: {info.filename}")
        names.add(folded)


def _read_office_member(archive: zipfile.ZipFile, name: str) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > MAX_OFFICE_MEMBER_BYTES:
        raise DocumentProcessingError(f"The Office document member is too large to process safely: {name}")
    return archive.read(info)


def _sheet_text(data: bytes, shared_strings: list[str]) -> str:
    root = ET.fromstring(data)
    rows = []
    for row in root.iter():
        if not row.tag.endswith("}row"):
            continue
        cells = []
        for cell in row:
            if not cell.tag.endswith("}c"):
                continue
            cell_type = cell.attrib.get("t")
            value = ""
            inline = next((node for node in cell.iter() if node.tag.endswith("}t") and node.text), None)
            raw = next((node for node in cell if node.tag.endswith("}v")), None)
            if inline is not None:
                value = inline.text or ""
            elif raw is not None and raw.text:
                value = raw.text
                if cell_type == "s":
                    try:
                        value = shared_strings[int(value)]
                    except (IndexError, ValueError):
                        pass
            if value.strip():
                cells.append(value.strip())
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _text_to_delimited(text: str, delimiter: str) -> str:
    lines = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        lines.append(delimiter.join(_escape_cell(cell, delimiter) for cell in cells))
    return "\n".join(lines) + "\n"


def _escape_cell(cell: str, delimiter: str) -> str:
    if any(char in cell for char in [delimiter, '"', "\n"]):
        return '"' + cell.replace('"', '""') + '"'
    return cell


def _clean_lines(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(line for line in lines if line).strip()
