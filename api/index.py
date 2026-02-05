import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías para PDF y Códigos de Barras
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, renderPDF

app = Flask(__name__, template_folder='../templates')

def generar_qr(c, x, y, tamaño, contenido):
    """Genera e inserta un código QR en el PDF"""
    qr_code = qr.QrCodeWidget(contenido)
    bounds = qr_code.getBounds()
    ancho = bounds[2] - bounds[0]
    alto = bounds[3] - bounds[1]
    d = Drawing(tamaño, tamaño, transform=[tamaño/ancho, 0, 0, tamaño/alto, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, c, x, y)

def separar_nombre(nombre_completo):
    """Divide el nombre en partes para la tabla central"""
    partes = nombre_completo.split()
    if len(partes) >= 3:
        paterno, materno, nombres = partes[-2], partes[-1], " ".join(partes[:-2])
    elif len(partes) == 2:
        nombres, paterno, materno = partes[0], partes[1], ""
    else:
        nombres, paterno, materno = nombre_completo, "", ""
    return nombres, paterno, materno

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validador')
def validador():
    """Página de validación que recibe D3 (idCIF_RFC)"""
    d3 = request.args.get('D3', '')
    idcif = d3.split("_")[0] if "_" in d3 else "23552656862"
    rfc = d3.split("_")[1] if "_" in d3 else "GOSJ960325862"
    
    datos = {
        "rfc": rfc,
        "idcif": idcif,
        "curp": rfc + "HDFNNL09"[:8],
        "nombre": "JULIO LEVI",
        "paterno": "GONZALEZ",
        "materno": "SANTELIZ",
        "situacion": "ACTIVO",
        "inicio_op": "25-12-2014",
        "entidad": "CIUDAD DE MÉXICO",
        "cp": "06700"
    }
    return render_template('validador.html', d=datos)

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Preparación de datos
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)
        fecha_const = "25 DE DICIEMBRE DE 2014"
        
        # URL Dinámica para el QR de la primera página
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        # 2. Mapeo de Coordenadas
        M = {
            "P1_QR": [74, 578, 82],
            "C_RFC": [165, 638], "C_NOM": [165, 612], "C_ID": [165, 595],
            "ID_X": 255, "ID_Y": 452, "ID_SKIP": 23.5,
            "H2_QR": [480, 80, 85],
            "H2_Y_ACT": 615, "H2_Y_REG": 530, "H2_X_FECHA": 485,
            "X_SELLOS": 60, "Y_CADENA": 115, "Y_SELLO": 85
        }

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Fuentes (Deben estar en carpeta /api)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        img1 = os.path.join(base_path, '..', 'plantilla.png')
        if os.path.exists(img1):
            c.drawImage(img1, 0, 0, width=612, height=792)

        # Insertar QR Redirigible
        generar_qr(c, M["P1_QR"][0], M["P1_QR"][1], M["P1_QR"][2], url_qr)

        # Datos Cédula
        c.setFont("SansBold", 8)
        c.drawCentredString(M["C_RFC"][0], M["C_RFC"][1], rfc)
        c.setFont("Sans", 6)
        c.drawCentredString(M["C_NOM"][0], M["C_NOM"][1], nombre_full)
        c.drawCentredString(M["C_ID"][0], M["C_ID"][1], f"idCIF: {idcif}")

        # Tabla Identificación
        c.setFont("Sans", 7)
        tx, ty, ts = M["ID_X"], M["ID_Y"], M["ID_SKIP"]
        datos_id = [rfc, curp, nombres, ape_pat, ape_mat, fecha_const, "ACTIVO", fecha_const, nombre_full]
        for i, val in enumerate(datos_id):
            c.drawString(tx, ty - (i * ts), str(val))

        c.showPage()

        # --- PÁGINA 2 ---
        img2 = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(img2):
            c.drawImage(img2, 0, 0, width=612, height=792)
            
            # QR de Página 2 (Texto informativo)
            generar_qr(c, M["H2_QR"][0], M["H2_QR"][1], M["H2_QR"][2], f"VALIDACION_SAT_{rfc}")

            c.setFont("Sans", 7)
            # Actividades y Regímenes
            c.drawString(90, M["H2_Y_ACT"], "Asalariado")
            c.drawString(M["H2_X_FECHA"], M["H2_Y_ACT"], fecha_const)
            c.drawString(60, M["H2_Y_REG"], "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
            c.drawString(M["H2_X_FECHA"], M["H2_Y_REG"], fecha_const)

            # Cadena y Sello
            c.setFont("Sans", 5)
            cadena = f"||1.1|{idcif}|{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}|{rfc}|{curp}||"
            sello = "".join(random.choices(string.ascii_letters + string.digits, k=115))
            c.drawString(M["X_SELLOS"], M["Y_CADENA"], "Cadena Original Sello:")
            c.drawString(M["X_SELLOS"], M["Y_CADENA"] - 7, cadena)
            c.drawString(M["X_SELLOS"], M["Y_SELLO"], "Sello Digital:")
            c.drawString(M["X_SELLOS"], M["Y_SELLO"] - 7, sello)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error en servidor: {str(e)}", 500
        
