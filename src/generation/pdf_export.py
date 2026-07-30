"""
Convert a generated .docx file to PDF. Uses docx2pdf, which drives
Microsoft Word via COM automation — Windows + Word only. On other
platforms (Linux cloud deployments, macOS, or Windows without Word),
PDF export is unavailable and docx_to_pdf() raises a clear, catchable
error instead of crashing at import time.
"""
import sys
from pathlib import Path

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    try:
        import pythoncom
        from docx2pdf import convert
        _PDF_EXPORT_AVAILABLE = True
    except ImportError:
        _PDF_EXPORT_AVAILABLE = False
else:
    _PDF_EXPORT_AVAILABLE = False


def docx_to_pdf(docx_path: str | Path, pdf_path: str | Path | None = None) -> Path:
    if not _PDF_EXPORT_AVAILABLE:
        raise RuntimeError(
            "PDF export is only available on Windows with Microsoft Word installed. "
            "This environment doesn't support it — download the .docx instead."
        )

    docx_path = Path(docx_path)
    if not docx_path.exists():
        raise FileNotFoundError(f"docx file not found: {docx_path}")

    if pdf_path is None:
        pdf_path = docx_path.with_suffix(".pdf")
    else:
        pdf_path = Path(pdf_path)

    pythoncom.CoInitialize()
    try:
        convert(str(docx_path), str(pdf_path))
    except Exception as e:
        raise RuntimeError(
            f"PDF conversion failed. This usually means Microsoft Word "
            f"is not installed or not accessible. Original error: {e}"
        )
    finally:
        pythoncom.CoUninitialize()

    return pdf_path


if __name__ == "__main__":
    import sys as _sys
    docx_file = _sys.argv[1] if len(_sys.argv) > 1 else "test_output_office.docx"
    result = docx_to_pdf(docx_file)
    print(f"Converted to: {result}")