from flask import Flask, request, send_file, render_template
from fpdf import FPDF
import io, os, qrcode
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

def pt_to_mm(pt):
    return pt * 0.352778

def draw_centered(pdf, x_pt, y_pt, text):
    x_mm = pt_to_mm(x_pt)
    y_mm = pt_to_mm(792 - y_pt)
    w = pdf.get_string_width(text)
    pdf.set_xy(x_mm - w / 2, y_mm)
    pdf.cell(w, 0, text)

class CSF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(False)

@app.route("/procesar", methods=["POST"])
def procesar():
    rfc = "PERJ82100497A"
    curp = "PERJ821004HDFRDR02"
    nombre = "JORGE ALDO PEREZ RODRIGUEZ"
    idcif = "21030308867"
    lugar_fecha = "CUAUHTEMOC, CIUDAD DE MEXICO, A 04 DE FEBRERO DE 2026"

    url_qr = f"https://{request.host}/validador?D3={idcif}_{rfc}"

    pdf = CSF()
    base = os.path.dirname(os.path.abspath(__file__))

    pdf.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"))
    pdf.add_font("SansBold", "", os.path.join(base, "DejaVuSans-Bold.ttf"))

    # ================== PÁGINA 1 ==================
    pdf.add_page()
    pdf.image(os.path.join(base, "../plantilla.png"), 0, 0, 215.9, 279.4)

    qr = qrcode.make(url_qr)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    pdf.image(qr_buf,
              pt_to_mm(74),
              pt_to_mm(792 - 578 - 82),
              pt_to_mm(82),
              pt_to_mm(82))

    pdf.set_font("SansBold", 8)
    draw_centered(pdf, 165, 638, rfc)

    pdf.set_font("Sans", 6.5)
    draw_centered(pdf, 165, 612, nombre)
    draw_centered(pdf, 165, 595, f"idCIF: {idcif}")

    pdf.set_font("SansBold", 7.5)
    draw_centered(pdf, 364, 683, lugar_fecha)

    # ================== PÁGINA 2 ==================
    pdf.add_page()
    pdf.image(os.path.join(base, "../plantilla2.png"), 0, 0, 215.9, 279.4)

    pdf.set_font("Sans", 7)
    pdf.set_xy(pt_to_mm(70), pt_to_mm(792 - 690))
    pdf.cell(0, 0, "Asalariado")

    out = pdf.output(dest="S").encode("latin1")
    return send_file(io.BytesIO(out),
                     mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"CSF_{rfc}.pdf")

@app.route("/validador")
def validador():
    return render_template("validador.html")
