from pathlib import Path

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph

from src.generation.preview import render_preview


def generate_pdf(form, output_path: str | Path):
    """
    Generate a PDF directly from the form preview.
    """

    output_path = Path(output_path)

    doc = SimpleDocTemplate(str(output_path))
    styles = getSampleStyleSheet()

    preview = render_preview(form)

    story = []

    for line in preview.split("\n"):
        if line.strip():
            story.append(Paragraph(line.replace(" ", "&nbsp;"), styles["Normal"]))
        else:
            story.append(Paragraph("<br/>", styles["Normal"]))

    doc.build(story)

    return output_path