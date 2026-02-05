import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, request, send_file, render_template
from fpdf import FPDF

app = Flask(__name__, template_folder='../templates')

def pt_to_mm(pt):
    return pt * 0.352778

class CSF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(False)

@app.route("/procesar", methods=["POST"])
def procesar():
    try:
        # --- DATOS ---
        nombre = request.form.get('nombre', 'JORGE ALDO PEREZ RODRIGUEZ').upper()
        curp = request.form.get('curp', 'PERJ821004HDFRDR02').upper()
        rfc = curp[:10] + "XX1" # Simulado
        idcif = "21030308867"
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        fecha_ini = "25 DE DICIEMBRE DE 2014"
        url_qr = f"https://{request.host}/validador?D3={idcif}_{rfc}"

        pdf = CSF()
        base = os.path.dirname(os.path.abspath(__file__))
        pdf.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"))
        pdf.add_font("SansBold", "", os.path.join(base, "DejaVuSans-Bold.ttf"))

        # ================== PÁGINA 1 ==================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla.png"), 0, 0, 215.9, 279.4)

        # QR Cédula
        qr = qrcode.make(url_qr)
        qr_buf = io.BytesIO()
        qr.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        pdf.image(qr_buf, x=pt_to_mm(74), y=pt_to_mm(792-578-82), w=pt_to_mm(82), h=pt_to_mm(82))

        # BLOQUE 1: CÉDULA (Centrado manual)
        pdf.set_font("SansBold", size=8)
        pdf.set_xy(pt_to_mm(165-50), pt_to_mm(792-638))
        pdf.cell(pt_to_mm(100), 0, rfc, align='C')

        pdf.set_font("Sans", size=6.5)
        pdf.set_xy(pt_to_mm(165-50), pt_to_mm(792-612))
        pdf.cell(pt_to_mm(100), 0, nombre, align='C')

        pdf.set_xy(pt_to_mm(165-50), pt_to_mm(792-595))
        pdf.cell(pt_to_mm(100), 0, f"idCIF: {idcif}", align='C')

        # LUGAR Y FECHA (Recuadro superior derecho)
        pdf.set_font("SansBold", size=7.5)
        pdf.set_xy(pt_to_mm(364-75), pt_to_mm(792-683))
        pdf.cell(pt_to_mm(150), 0, lugar_fecha, align='C')

        # BLOQUE 2: IDENTIFICACIÓN (Coordenadas exactas)
        pdf.set_font("Sans", size=7)
        datos_id = [rfc, curp, "JORGE ALDO", "PEREZ", "RODRIGUEZ", fecha_ini, "ACTIVO", fecha_ini, ""]
        y_fix = 452
        for d in datos_id:
            pdf.set_xy(pt_to_mm(255), pt_to_mm(792-y_fix))
            pdf.cell(100, 0, str(d))
            y_fix -= 23.5

        # BLOQUE 3: DOMICILIO
        pdf.set_font("Sans", size=6.5)
        filas_y = [284, 263, 242, 221, 200]
        col_izq = ["06700", "INSURGENTES", "S/N", "CUAUHTÉMOC", "CIUDAD DE MÉXICO"]
        col_der = ["CALZADA", "880", "ROMA NORTE", "CUAUHTÉMOC", "CALLE 10 Y 12"]
        
        for i in range(len(filas_y)):
            pdf.set_xy(pt_to_mm(120), pt_to_mm(792-filas_y[i]))
            pdf.cell(80, 0, col_izq[i])
            pdf.set_xy(pt_to_mm(430), pt_to_mm(792-filas_y[i]))
            pdf.cell(80, 0, col_der[i])

        # ================== PÁGINA 2 ==================
        pdf.add_page()
        pdf.image(os.path.join(base, "../plantilla2.png"), 0, 0, 215.9, 279.4)

        # BLOQUE 4: ACTIVIDADES (Coordenadas X: 45, 90, 415, 485 | Y: 615)
        pdf.set_font("Sans", size=7)
        y_act = 615
        pdf.set_xy(pt_to_mm(45), pt_to_mm(792-y_act)); pdf.cell(10, 0, "1")
        pdf.set_xy(pt_to_mm(90), pt_to_mm(792-y_act)); pdf.cell(100, 0, "Asalariado")
        pdf.set_xy(pt_to_mm(415), pt_to_mm(792-y_act)); pdf.cell(20, 0, "100")
        pdf.set_xy(pt_to_mm(485), pt_to_mm(792-y_act)); pdf.cell(40, 0, fecha_ini)

        # BLOQUE 5: REGÍMENES (X: 60, 485 | Y: 530)
        y_reg = 530
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792-y_reg))
        pdf.cell(150, 0, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        pdf.set_xy(pt_to_mm(485), pt_to_mm(792-y_reg))
        pdf.cell(40, 0, fecha_ini)

        # BLOQUE 6: SELLOS Y QR FINAL
        pdf.set_font("SansBold", size=6)
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792-125)); pdf.cell(100, 0, "Cadena Original Sello:")
        pdf.set_font("Sans", size=5)
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792-118))
        pdf.cell(180, 0, f"||1.1|CSF|{idcif}|{datetime.now().isoformat()}|{rfc}||")
        
        qr_buf.seek(0)
        pdf.image(qr_buf, x=pt_to_mm(480), y=pt_to_mm(792-80-85), w=pt_to_mm(85), h=pt_to_mm(85))

        # --- GENERACIÓN ---
        output = pdf.output()
        return send_file(io.BytesIO(output), mimetype="application/pdf", as_attachment=True, download_name=f"CSF_{rfc}.pdf")

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/")
def index(): return render_template("index.html")

@app.route("/validador")
def validador(): return render_template("validador.html")
