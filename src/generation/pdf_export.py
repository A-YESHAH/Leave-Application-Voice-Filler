"""
Convert a generated .docx file to PDF. Uses docx2pdf, which drives
Microsoft Word via COM automation on Windows. Requires Word to be
installed. Explicitly initializes COM on the calling thread, since
docx2pdf can fail with 'CoInitialize has not been called' when run
inside a threaded context like Streamlit's script execution.
"""
from pathlib import Path
import pythoncom
from docx2pdf import convert


def docx_to_pdf(docx_path: str | Path, pdf_path: str | Path | None = None) -> Path:
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
    import sys
    docx_file = sys.argv[1] if len(sys.argv) > 1 else "test_output_office.docx"
    result = docx_to_pdf(docx_file)
    print(f"Converted to: {result}")