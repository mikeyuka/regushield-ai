import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "app", "templates")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def compile_pdf_blueprint(product_data: dict, validation_results: list, output_filename: str) -> str:
    """
    Renders the blueprint Jinja2 template and attempts to compile it into a PDF
    using WeasyPrint. Falls back to raw HTML if WeasyPrint is unavailable.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Initialize Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("blueprint_template.html")

    # Render template
    context = {
        "header_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "product": product_data,
        "validation_results": validation_results
    }
    rendered_html = template.render(context)

    try:
        # Attempt to import and use WeasyPrint
        from weasyprint import HTML
        pdf_path = os.path.join(UPLOAD_DIR, output_filename)
        HTML(string=rendered_html).write_pdf(pdf_path)
        return f"/static/{output_filename}"
    except Exception:
        # Catch any ImportError or runtime failures due to missing binaries
        base_name, _ = os.path.splitext(output_filename)
        html_filename = f"{base_name}.html"
        html_path = os.path.join(UPLOAD_DIR, html_filename)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        return f"/static/{html_filename}"
