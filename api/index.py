import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, render_template, request, send_file
from fpdf import FPDF

app = Flask(__name__, template_folder='../templates')

# ---- Conversión pt → mm (ReportLab → FPDF)
def pt_to_mm(pt):
    return pt * 0.352778

class CSF_PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(auto=False)

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # ---------------- DATOS ----------------
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()

        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))

        lugar_fecha_txt = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        fecha_f = "25 DE DICIEMBRE DE 2014"

        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        # ---------------- PDF ----------------
        pdf = CSF_PDF()
        base = os.path.dirname(os.path.abspath(__file__))

        # Fuentes
        pdf.add_font("Sans", "", os.path.join(base, "DejaVuSans.ttf"))
        pdf.add_font("SansBold", "", os.path.join(base, "DejaVuSans-Bold.ttf"))

        # ================= PÁGINA 1 =================
        pdf.add_page()
        pdf.image(os.path.join(base, '..', 'plantilla.png'), x=0, y=0, w=215.9, h=279.4)

        # ---- QR
        qr_img = qrcode.make(url_qr)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        pdf.image(
            qr_buffer,
            x=pt_to_mm(74),
            y=pt_to_mm(792 - 578 - 82),
            w=pt_to_mm(82),
            h=pt_to_mm(82)
        )

        # ---- RFC (centrado real)
        pdf.set_font("SansBold", size=8)
        pdf.set_xy(0, pt_to_mm(792 - 638))
        pdf.cell(0, 0, rfc, align='C')

        # ---- Nombre
        pdf.set_font("Sans", size=6.5)
        pdf.set_xy(0, pt_to_mm(792 - 612))
        pdf.cell(0, 0, nombre_full, align='C')

        # ---- idCIF
        pdf.set_xy(0, pt_to_mm(792 - 595))
        pdf.cell(0, 0, f"idCIF: {idcif}", align='C')

        # ---- Lugar y Fecha
        pdf.set_font("SansBold", size=7.5)
        pdf.set_xy(0, pt_to_mm(792 - 683))
        pdf.cell(0, 0, lugar_fecha_txt, align='C')

        # ---- Identificación del contribuyente
        pdf.set_font("Sans", size=7)
        campos_id = [
            rfc, curp, nombre_full, "", "", fecha_f, "ACTIVO", fecha_f, ""
        ]

        y_id = 452
        for val in campos_id:
            pdf.set_xy(pt_to_mm(255), pt_to_mm(792 - y_id))
            pdf.cell(pt_to_mm(200), 0, str(val))
            y_id -= 23.5

        # ---- Domicilio fiscal
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
            pdf.cell(pt_to_mm(120), 0, f[1])
            pdf.set_xy(pt_to_mm(f[2]), pt_to_mm(792 - y_dom))
            pdf.cell(pt_to_mm(150), 0, f[3])
            y_dom -= 21

        # ================= PÁGINA 2 =================
        pdf.add_page()
        pdf.image(os.path.join(base, '..', 'plantilla2.png'), x=0, y=0, w=215.9, h=279.4)

        # ---- Actividades
        pdf.set_font("Sans", size=7)
        y_act = 615
        pdf.set_xy(pt_to_mm(45), pt_to_mm(792 - y_act)); pdf.cell(0, 0, "1")
        pdf.set_xy(pt_to_mm(90), pt_to_mm(792 - y_act)); pdf.cell(0, 0, "Asalariado")
        pdf.set_xy(pt_to_mm(415), pt_to_mm(792 - y_act)); pdf.cell(0, 0, "100")
        pdf.set_xy(pt_to_mm(485), pt_to_mm(792 - y_act)); pdf.cell(0, 0, fecha_f)

        # ---- Regímenes
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792 - 530))
        pdf.cell(pt_to_mm(330), 0, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        pdf.set_xy(pt_to_mm(485), pt_to_mm(792 - 530))
        pdf.cell(0, 0, fecha_f)

        # ---- Sellos
        pdf.set_font("SansBold", size=6)
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792 - 125))
        pdf.cell(0, 0, "Cadena Original Sello:")

        pdf.set_font("Sans", size=5)
        pdf.set_xy(pt_to_mm(60), pt_to_mm(792 - 118))
        pdf.cell(pt_to_mm(350), 0,
                 f"||1.1|CSF|{idcif}|{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}|{rfc}||")

        # ---- QR página 2
        qr_buffer.seek(0)
        pdf.image(
            qr_buffer,
            x=pt_to_mm(480),
            y=pt_to_mm(792 - 80 - 85),
            w=pt_to_mm(85),
            h=pt_to_mm(85)
        )

        # ---------------- SALIDA ----------------
        pdf_output = pdf.output(dest='S').encode('latin1')
        return send_file(
            io.BytesIO(pdf_output),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'CSF_{rfc}.pdf'
        )

    except Exception as e:
        return f"Error FPDF2: {str(e)}", 500


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/validador')
def validador():
    d3 = request.args.get('D3', '')
    rfc = d3.split("_")[1] if "_" in d3 else "PERJ82100497A"
    return render_template('validador.html', d={"rfc": rfc, "situacion": "ACTIVO"})
