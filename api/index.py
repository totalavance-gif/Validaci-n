import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, request, send_file, render_template
from fpdf import FPDF

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE PRECISIÓN ---
AJUSTE_Y_FINO = -0.8  # Ajuste para compensar el renderizado de la fuente (en mm)
PT_TO_MM = 0.352778

def get_y_mm(y_pt):
    # Invierte el eje Y (792pt es el alto de Letter) y convierte a mm
    return (792 - y_pt) * PT_TO_MM + AJUSTE_Y_FINO

def pos_abs(pdf, x_pt, y_pt):
    """Posiciona el cursor en coordenadas exactas de ReportLab."""
    pdf.set_xy(x_pt * PT_TO_MM, get_y_mm(y_pt))

def draw_center_abs(pdf, x_pt, y_pt, text):
    """Réplica exacta de drawCentredString."""
    w_text = pdf.get_string_width(text)
    x_mm = (x_pt * PT_TO_MM) - (w_text / 2)
    pdf.set_xy(x_mm, get_y_mm(y_pt))
    pdf.write(0, text)

class CSF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        # REGLA 1: Anular márgenes y salto automático
        self.set_margins(0, 0, 0)
        self.set_auto_page_break(False)

@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        # Datos (puedes volver a hacerlos dinámicos con request.form)
        nombre = request.form.get('nombre', 'JORGE ALDO PEREZ RODRIGUEZ').upper()
        curp = request.form.get('curp', 'PERJ821004HDFRDR02').upper()
        rfc = curp[:10] + "XX1"
        idcif = "21030308867"
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        url_qr = f"https://{request.host}/validador?D3={idcif}_{rfc}"

        pdf = CSF()
        base = os.path.dirname(os.path.abspath(__file__))
        pdf.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"))
        pdf.add_font("SansBold", "", os.path.join(base, "DejaVuSans-Bold.ttf"))

        # ================== PÁGINA 1 ==================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla.png"), 0, 0, 215.9, 279.4)

        # QR Cédula (Posición absoluta)
        qr = qrcode.make(url_qr)
        qr_buf = io.BytesIO(); qr.save(qr_buf, format="PNG"); qr_buf.seek(0)
        pdf.image(qr_buf, x=74 * PT_TO_MM, y=(792-578-82) * PT_TO_MM, w=82 * PT_TO_MM, h=82 * PT_TO_MM)

        # BLOQUE 1: CÉDULA (Centrados reales)
        pdf.set_font("SansBold", size=8)
        draw_center_abs(pdf, 165, 638, rfc)
        
        pdf.set_font("Sans", size=6.5)
        draw_center_abs(pdf, 165, 612, nombre)
        draw_center_abs(pdf, 165, 595, f"idCIF: {idcif}")

        pdf.set_font("SansBold", size=7.5)
        draw_center_abs(pdf, 364, 683, lugar_fecha)

        # BLOQUE 2: IDENTIFICACIÓN (Uso de write() para evitar saltos de cell)
        pdf.set_font("Sans", size=7)
        y_id = 452
        datos_id = [rfc, curp, "JORGE ALDO", "PEREZ", "RODRIGUEZ", "25 DE DICIEMBRE DE 2014", "ACTIVO", "25 DE DICIEMBRE DE 2014", ""]
        for d in datos_id:
            pos_abs(pdf, 255, y_id)
            pdf.write(0, str(d))
            y_id -= 23.5

        # BLOQUE 3: DOMICILIO (Mapeo directo)
        pdf.set_font("Sans", size=6.5)
        filas_y = [284, 263, 242, 221, 200]
        col_izq = ["06700", "INSURGENTES", "S/N", "CUAUHTÉMOC", "CIUDAD DE MÉXICO"]
        col_der = ["CALZADA", "880", "ROMA NORTE", "CUAUHTÉMOC", "CALLE 10 Y 12"]
        
        for i in range(len(filas_y)):
            pos_abs(pdf, 120, filas_y[i])
            pdf.write(0, col_izq[i])
            pos_abs(pdf, 430, filas_y[i])
            pdf.write(0, col_der[i])

        # ================== PÁGINA 2 ==================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla2.png"), 0, 0, 215.9, 279.4)

        # Actividades
        pdf.set_font("Sans", size=7)
        pos_abs(pdf, 45, 615); pdf.write(0, "1")
        pos_abs(pdf, 90, 615); pdf.write(0, "Asalariado")
        pos_abs(pdf, 415, 615); pdf.write(0, "100")
        pos_abs(pdf, 485, 615); pdf.write(0, "25 DE DICIEMBRE DE 2014")

        # Regímenes
        pos_abs(pdf, 60, 530); pdf.write(0, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        pos_abs(pdf, 485, 530); pdf.write(0, "25 DE DICIEMBRE DE 2014")

        # Sellos (X=60)
        pdf.set_font("SansBold", size=6)
        pos_abs(pdf, 60, 125); pdf.write(0, "Cadena Original Sello:")
        pdf.set_font("Sans", size=5)
        pos_abs(pdf, 60, 118); pdf.write(0, f"||1.1|CSF|{idcif}|{datetime.now().isoformat()}|{rfc}||")

        # QR P2
        qr_buf.seek(0)
        pdf.image(qr_buf, x=480 * PT_TO_MM, y=(792-80-85) * PT_TO_MM, w=85 * PT_TO_MM, h=85 * PT_TO_MM)

        return send_file(io.BytesIO(pdf.output()), mimetype="application/pdf", as_attachment=True, download_name=f"CSF_{rfc}.pdf")

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/")
def index(): return render_template("index.html")

@app.route("/validador")
def validador(): return render_template("validador.html")
        
