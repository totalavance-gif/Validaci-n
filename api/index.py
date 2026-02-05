from flask import Flask, request, send_file, render_template
from fpdf import FPDF
import io, os, qrcode, random, string
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# ---- Conversión pt → mm
def pt_to_mm(pt):
    return pt * 0.352778

# ---- Función de centrado dinámico
def draw_centered(pdf, x_pt, y_pt, text):
    x_mm = pt_to_mm(x_pt)
    y_mm = pt_to_mm(792 - y_pt)
    # Calcula el ancho del texto con la fuente actual
    w_text = pdf.get_string_width(text)
    # Posiciona para que el centro del texto sea x_mm
    pdf.set_xy(x_mm - (w_text / 2), y_mm)
    pdf.cell(w_text, 0, text)

class CSF(FPDF):
    def __init__(self):
        # Letter size: 215.9 x 279.4 mm
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(False)

@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        # Obtener datos del formulario
        nombre_form = request.form.get('nombre', 'JORGE ALDO PEREZ RODRIGUEZ').upper()
        curp_form = request.form.get('curp', 'PERJ821004HDFRDR02').upper()
        
        # Generar datos simulados
        rfc = curp_form[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        url_qr = f"https://{request.host}/validador?D3={idcif}_{rfc}"

        pdf = CSF()
        base = os.path.dirname(os.path.abspath(__file__))

        # Registrar fuentes (Asegúrate de que los archivos estén en api/)
        pdf.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"))
        pdf.add_font("SansBold", "", os.path.join(base, "DejaVuSans-Bold.ttf"))

        # ================== PÁGINA 1 ==================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla.png"), 0, 0, 215.9, 279.4)

        # Generar QR
        qr = qrcode.make(url_qr)
        qr_buf = io.BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)

        # QR Cédula
        pdf.image(qr_buf, pt_to_mm(74), pt_to_mm(792 - 578 - 82), pt_to_mm(82), pt_to_mm(82))

        # Textos Centrados Cédula
        pdf.set_font("SansBold", size=8)
        draw_centered(pdf, 165, 638, rfc)

        pdf.set_font("Sans", size=6.5)
        draw_centered(pdf, 165, 612, nombre_form)
        draw_centered(pdf, 165, 595, f"idCIF: {idcif}")

        # Lugar y Fecha Emisión
        pdf.set_font("SansBold", size=7.5)
        draw_centered(pdf, 364, 683, lugar_fecha)

        # Datos de Identificación (Columna fija a la izquierda)
        pdf.set_font("Sans", size=7)
        y_id = 452
        # RFC, CURP, Nombre, Pat, Mat, Inicio, Estatus, Cambio, Comercial
        datos = [rfc, curp_form, nombre_form, "", "", "25 DE DICIEMBRE DE 2014", "ACTIVO", "25 DE DICIEMBRE DE 2014", ""]
        for dato in datos:
            pdf.set_xy(pt_to_mm(255), pt_to_mm(792 - y_id))
            pdf.cell(0, 0, str(dato))
            y_id -= 23.5

        # ================== PÁGINA 2 ==================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla2.png"), 0, 0, 215.9, 279.4)

        # Actividades Económicas
        pdf.set_font("Sans", size=7)
        pdf.set_xy(pt_to_mm(90), pt_to_mm(792 - 615))
        pdf.cell(0, 0, "Asalariado")
        
        # QR Página 2
        qr_buf.seek(0)
        pdf.image(qr_buf, pt_to_mm(480), pt_to_mm(792 - 80 - 85), pt_to_mm(85), pt_to_mm(85))

        # Salida segura
        out = pdf.output() 
        return send_file(io.BytesIO(out),
                         mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"CSF_{rfc}.pdf")

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/")
def index(): return render_template("index.html")

@app.route("/validador")
def validador(): return render_template("validador.html")
    
