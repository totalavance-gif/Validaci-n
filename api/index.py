import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, request, send_file, render_template
from fpdf import FPDF

app = Flask(__name__, template_folder='../templates')

# ---- Utilidades de Conversión y Posicionamiento ----
def pt_to_mm(pt):
    return pt * 0.352778

def draw_centered(pdf, x_pt, y_pt, text):
    """Calcula el ancho real del texto para centrarlo exactamente en x_pt."""
    x_mm = pt_to_mm(x_pt)
    y_mm = pt_to_mm(792 - y_pt)
    w_text = pdf.get_string_width(text)
    pdf.set_xy(x_mm - (w_text / 2), y_mm)
    pdf.cell(w_text, 0, text)

class CSF_PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(False)

@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        # 1. Recuperación de datos del formulario
        curp = request.form.get('curp', 'PERJ821004HDFRDR02').upper()
        nombre_full = request.form.get('nombre', 'JORGE ALDO PEREZ RODRIGUEZ').upper()
        
        # 2. Generación de datos dinámicos
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        fecha_ini = "25 DE DICIEMBRE DE 2014"
        url_qr = f"https://{request.host}/validador?D3={idcif}_{rfc}"

        # 3. Configuración del PDF
        pdf = CSF_PDF()
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de fuentes (Asegúrate que los archivos .ttf estén en api/)
        pdf.add_font("Sans", "", os.path.join(base_path, "DejaVuSans.ttf"))
        pdf.add_font("SansBold", "", os.path.join(base_path, "DejaVuSans-Bold.ttf"))

        # ================== PÁGINA 1 ==================
        pdf.add_page()
        pdf.image(os.path.join(base_path, "../plantilla.png"), 0, 0, 215.9, 279.4)

        # Generación de código QR
        qr_gen = qrcode.make(url_qr)
        qr_buf = io.BytesIO()
        qr_gen.save(qr_buf, format="PNG")
        qr_buf.seek(0)

        # Bloque 1: Cédula Superior
        pdf.image(qr_buf, pt_to_mm(74), pt_to_mm(792 - 578 - 82), pt_to_mm(82), pt_to_mm(82))
        
        pdf.set_font("SansBold", size=8)
        draw_centered(pdf, 165, 638, rfc)
        
        pdf.set_font("Sans", size=6.5)
        draw_centered(pdf, 165, 612, nombre_full)
        draw_centered(pdf, 165, 595, f"idCIF: {idcif}")
        
        pdf.set_font("SansBold", size=7.5)
        draw_centered(pdf, 364, 683, lugar_fecha)

        # Bloque 2: Identificación del Contribuyente
        pdf.set_font("Sans", size=7)
        y_id = 452
        datos_id = [rfc, curp, nombre_full, "", "", fecha_ini, "ACTIVO", fecha_ini, ""]
        for dato in datos_id:
            pdf.set_xy(pt_to_mm(255), pt_to_mm(792 - y_id))
            pdf.cell(0, 0, str(dato))
            y_id -= 23.5

        # Bloque 3: Domicilio Fiscal
        pdf.set_font("Sans", size=6.5)
        y_dom = 284
        filas_dom = [
            (120, "06700", 430, "CALZADA"),
            (120, "INSURGENTES", 430, "880"),
            (120, "S/N", 430, "ROMA NORTE"),
            (120, "CUAUHTÉMOC", 430, "CUAUHTÉMOC"),
            (120, "CIUDAD DE MÉXICO", 430, "CALLE 10 Y 12")
        ]
        for f in filas_dom:
            pdf.set_xy(pt_to_mm(f[0]), pt_to_mm(792 - y_dom))
            pdf.cell(0, 0, f[1])
            pdf.set_xy(pt_to_mm(f[2]), pt_to_mm(792 - y_dom))
            pdf.cell(0, 0, f[3])
            y_dom -= 21

        # ================== PÁGINA 2 ==================
        pdf.add_page()
        pdf.image(os.path.join(base_path, "../plantilla2.png"), 0, 0, 215.9, 279.4)

        # Bloque 4: Actividades Económicas
        pdf.set_font("Sans", size=7)
        pdf.set_xy(pt_to_mm(45), pt_to_mm(792 - 615)); pdf.cell(0, 0, "1")
        pdf.set_xy(pt_to_mm(90), pt_to_mm(792 - 615)); pdf.cell(0, 0, "Asalariado")
        pdf.set_xy(pt_to_mm(415), pt_to_mm(792 - 615)); pdf.cell(0, 0, "100")
        pdf.set_xy(pt_to_mm(485), pt_to_mm(792 - 615)); pdf.cell(0, 0, fecha_ini)

        # Bloque 5: Regímenes Fiscales
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792 - 530))
        pdf.cell(0, 0, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        pdf.set_xy(pt_to_mm(485), pt_to_mm(792 - 530))
        pdf.cell(0, 0, fecha_ini)

        # Bloque 6: Sellos Digitales y QR P2
        pdf.set_font("SansBold", size=6)
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792 - 125)); pdf.cell(0, 0, "Cadena Original Sello:")
        pdf.set_font("Sans", size=5)
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792 - 118))
        pdf.cell(0, 0, f"||1.1|CSF|{idcif}|{datetime.now().isoformat()}|{rfc}||")
        
        qr_buf.seek(0)
        pdf.image(qr_buf, pt_to_mm(480), pt_to_mm(792 - 80 - 85), pt_to_mm(85), pt_to_mm(85))

        # 4. Finalización y Retorno
        output = pdf.output()
        return send_file(
            io.BytesIO(output),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"CSF_{rfc}.pdf"
        )

    except Exception as e:
        return f"Error en generación FPDF2: {str(e)}", 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/validador")
def validador():
    return render_template("validador.html")

if __name__ == "__main__":
    app.run(debug=True)
        
