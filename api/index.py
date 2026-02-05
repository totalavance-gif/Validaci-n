import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

app = Flask(__name__, template_folder='../templates')

# CONFIGURACIÓN MAESTRA (Tu JSON convertido a diccionario)
MAPEO = {
    "cedula": {
        "qr": {"x": 74, "y": 578, "w": 82, "h": 82},
        "rfc": {"xc": 165, "y": 638, "f": "SansBold", "s": 8},
        "nombre": {"xc": 165, "y": 612, "f": "Sans", "s": 6.5},
        "idcif": {"xc": 165, "y": 595, "f": "Sans", "s": 6.5, "pre": "idCIF: "},
        "lugar_fecha": {"xc": 364, "y": 683, "f": "SansBold", "s": 7.5}
    },
    "identificacion": {"x": 255, "y": 452, "step": 23.5, "f": "Sans", "s": 7},
    "domicilio": {"y_ini": 284, "step": 21.0, "x_izq": 120, "x_der": 430, "f": "Sans", "s": 6.5},
    "hoja2": {
        "act": {"y": 615, "col": [45, 90, 415, 485], "f": "Sans", "s": 7},
        "reg": {"y": 530, "col": [60, 485], "f": "Sans", "s": 7},
        "sellos": {
            "x": 60, "cy": 125, "cv": 118, "sy": 95, "sv": 88,
            "ft": "SansBold", "st": 6, "fc": "Sans", "sc": 5
        },
        "qr": {"x": 480, "y": 80, "w": 85, "h": 85}
    }
}

def obtener_qr_img(contenido):
    qr_gen = qrcode.QRCode(box_size=10, border=0)
    qr_gen.add_data(contenido)
    qr_gen.make(fit=True)
    img = qr_gen.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO(); img.save(img_byte_arr, format='PNG'); img_byte_arr.seek(0)
    return img_byte_arr

def separar_nombre(nombre_full):
    p = nombre_full.split()
    return (" ".join(p[:-2]), p[-2], p[-1]) if len(p) >= 3 else (nombre_full, "", "")

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Preparación de Datos
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nom, pat, mat = separar_nombre(nombre_full)
        fecha_f = "25 DE DICIEMBRE DE 2014"
        lugar_f = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=letter)
        base = os.path.dirname(os.path.abspath(__file__))
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        c.drawImage(os.path.join(base, '..', 'plantilla.png'), 0, 0, 612, 792)
        
        # Bloque Cédula
        m1 = MAPEO["cedula"]
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), m1["qr"]["x"], m1["qr"]["y"], m1["qr"]["w"], m1["qr"]["h"])
        c.setFont(m1["rfc"]["f"], m1["rfc"]["s"]); c.drawCentredString(m1["rfc"]["xc"], m1["rfc"]["y"], rfc)
        c.setFont(m1["nombre"]["f"], m1["nombre"]["s"]); c.drawCentredString(m1["nombre"]["xc"], m1["nombre"]["y"], nombre_full)
        c.setFont(m1["idcif"]["f"], m1["idcif"]["s"]); c.drawCentredString(m1["idcif"]["xc"], m1["idcif"]["y"], f"{m1['idcif']['pre']}{idcif}")
        c.setFont(m1["lugar_fecha"]["f"], m1["lugar_fecha"]["s"]); c.drawCentredString(m1["lugar_fecha"]["xc"], m1["lugar_fecha"]["y"], lugar_f)

        # Bloque Identificación
        m2 = MAPEO["identificacion"]
        c.setFont(m2["f"], m2["s"])
        d_id = [rfc, curp, nom, pat, mat, fecha_f, "ACTIVO", fecha_f, " "]
        for i, val in enumerate(d_id): c.drawString(m2["x"], m2["y"] - (i * m2["step"]), str(val))

        # Bloque Domicilio
        m3 = MAPEO["domicilio"]
        c.setFont(m3["f"], m3["s"])
        filas = [["06700", "CALZADA"], ["INSURGENTES", "880"], ["S/N", "ROMA NORTE"], ["CUAUHTÉMOC", "CUAUHTÉMOC"], ["CIUDAD DE MÉXICO", "CALLE 10 Y 12"]]
        for i, f in enumerate(filas):
            c.drawString(m3["x_izq"], m3["y_ini"] - (i * m3["step"]), f[0])
            c.drawString(m3["x_der"], m3["y_ini"] - (i * m3["step"]), f[1])

        c.showPage()

        # --- PÁGINA 2 ---
        c.drawImage(os.path.join(base, '..', 'plantilla2.png'), 0, 0, 612, 792)
        m4 = MAPEO["hoja2"]
        
        # Actividades y Regímenes
        c.setFont(m4["act"]["f"], m4["act"]["s"])
        for x, val in zip(m4["act"]["col"], ["1", "Asalariado", "100", fecha_f]): c.drawString(x, m4["act"]["y"], val)
        for x, val in zip(m4["reg"]["col"], ["Régimen de Sueldos y Salarios", fecha_f]): c.drawString(x, m4["reg"]["y"], val)

        # Sellos
        s = m4["sellos"]
        c.setFont(s["ft"], s["st"]); c.drawString(s["x"], s["cy"], "Cadena Original Sello:")
        c.setFont(s["fc"], s["sc"]); c.drawString(s["x"], s["cv"], f"||1.1|{idcif}|{datetime.now().isoformat()}|{rfc}||")
        c.setFont(s["ft"], s["st"]); c.drawString(s["x"], s["sy"], "Sello Digital:")
        c.setFont(s["fc"], s["sc"]); c.drawString(s["x"], s["sv"], "".join(random.choices(string.ascii_letters + string.digits, k=115)))
        
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), m4["qr"]["x"], m4["qr"]["y"], m4["qr"]["w"], m4["qr"]["h"])

        c.save(); buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')
    except Exception as e: return f"Error: {str(e)}", 500

@app.route('/')
def index(): return render_template('index.html')

@app.route('/validador')
def validador():
    d3 = request.args.get('D3', '')
    rfc = d3.split("_")[1] if "_" in d3 else "PERJ82100497A"
    return render_template('validador.html', d={"rfc": rfc, "situacion": "ACTIVO"})
