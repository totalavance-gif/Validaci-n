import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, request, send_file, render_template
from fpdf import FPDF

app = Flask(__name__, template_folder="../templates")

# ================= CONFIG =================
PT_TO_MM = 0.352778  # conversión real pt → mm (72dpi)

def xy(pdf, x_pt, y_pt):
    """Posición absoluta FPDF (origen arriba-izquierda)."""
    pdf.set_xy(x_pt * PT_TO_MM, y_pt * PT_TO_MM)

def center(pdf, x_pt, y_pt, text):
    """Equivalente a drawCentredString pero en FPDF."""
    w = pdf.get_string_width(text)
    x_mm = (x_pt * PT_TO_MM) - (w / 2)
    y_mm = y_pt * PT_TO_MM
    pdf.set_xy(x_mm, y_mm)
    pdf.write(0, text)

class CSF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.set_margins(0, 0, 0)
        self.set_auto_page_break(False)

# ================= ROUTES =================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        # -------- DATOS --------
        nombre = request.form.get("nombre", "").upper()
        curp = request.form.get("curp", "").upper()

        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        fecha_inicio = "25 DE DICIEMBRE DE 2014"
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"

        url_qr = f"https://{request.host}/validador?D3={idcif}_{rfc}"

        base = os.path.dirname(os.path.abspath(__file__))
        pdf = CSF()

        # Fuentes
        pdf.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"), uni=True)
        pdf.add_font("SansBold", "", os.path.join(base, "DejaVuSans-Bold.ttf"), uni=True)

        # ================= PÁGINA 1 =================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla.png"), 0, 0, 215.9, 279.4)

        # QR superior
        qr = qrcode.make(url_qr)
        qr_buf = io.BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        pdf.image(qr_buf, x=74*PT_TO_MM, y=578*PT_TO_MM, w=82*PT_TO_MM, h=82*PT_TO_MM)

        # ---- CÉDULA ----
        pdf.set_font("SansBold", size=8)
        center(pdf, 165, 638, rfc)

        pdf.set_font("Sans", size=6.5)
        center(pdf, 165, 612, nombre)
        center(pdf, 165, 595, f"idCIF: {idcif}")

        pdf.set_font("SansBold", size=7.5)
        center(pdf, 364, 683, lugar_fecha)

        # ---- IDENTIFICACIÓN ----
        pdf.set_font("Sans", size=7)
        y = 452
        datos = [
            rfc,
            curp,
            nombre.split(" ")[0],
            nombre.split(" ")[1] if len(nombre.split()) > 1 else "",
            nombre.split(" ")[2] if len(nombre.split()) > 2 else "",
            fecha_inicio,
            "ACTIVO",
            fecha_inicio,
            ""
        ]
        for d in datos:
            xy(pdf, 255, y)
            pdf.write(0, d)
            y += 23.5

        # ---- DOMICILIO ----
        pdf.set_font("Sans", size=6.5)
        filas = [
            (284, "06700", "CALZADA"),
            (263, "INSURGENTES", "880"),
            (242, "S/N", "ROMA NORTE"),
            (221, "CUAUHTÉMOC", "CUAUHTÉMOC"),
            (200, "CIUDAD DE MÉXICO", "CALLE 10 Y 12")
        ]
        for y, izq, der in filas:
            xy(pdf, 120, y)
            pdf.write(0, izq)
            xy(pdf, 430, y)
            pdf.write(0, der)

        # ================= PÁGINA 2 =================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla2.png"), 0, 0, 215.9, 279.4)

        pdf.set_font("Sans", size=7)
        xy(pdf, 45, 615); pdf.write(0, "1")
        xy(pdf, 90, 615); pdf.write(0, "Asalariado")
        xy(pdf, 415, 615); pdf.write(0, "100")
        xy(pdf, 485, 615); pdf.write(0, fecha_inicio)

        xy(pdf, 60, 530)
        pdf.write(0, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        xy(pdf, 485, 530)
        pdf.write(0, fecha_inicio)

        # ---- SELLOS ----
        pdf.set_font("SansBold", size=6)
        xy(pdf, 60, 125)
        pdf.write(0, "Cadena Original Sello:")

        pdf.set_font("Sans", size=5)
        xy(pdf, 60, 118)
        pdf.write(0, f"||1.1|{idcif}|{datetime.now().isoformat()}|{rfc}||")

        # QR página 2
        qr_buf.seek(0)
        pdf.image(qr_buf, x=480*PT_TO_MM, y=80*PT_TO_MM, w=85*PT_TO_MM, h=85*PT_TO_MM)

        # -------- SALIDA --------
        return send_file(
            io.BytesIO(pdf.output()),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"CSF_{rfc}.pdf"
        )

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/validador")
def validador():
    return render_template("validador.html")
