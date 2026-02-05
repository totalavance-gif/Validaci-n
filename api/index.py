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

def dibujar_qr(c, x, y, size, data):
    """Función para generar los QR dinámicamente"""
    qr_code = qr.QrCodeWidget(data)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(size, size, transform=[size/width, 0, 0, size/height, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, c, x, y)

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Datos del Formulario
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))

        # =========================================================
        # PANEL DE CONTROL DE COORDENADAS (MODIFICA AQUÍ)
        # Formato: [X, Y, Tamaño]
        # =========================================================
        M = {
            # --- PÁGINA 1 ---
            "QR_CEDULA":      [74,  578, 80],   # QR de la página 1
            "CEDULA_RFC":     [165, 638, 8],    # RFC centrado en cuadro
            "CEDULA_NOM":     [165, 612, 6],    # Nombre centrado en cuadro
            "FECHA_EMI":      [585, 683, 7],    # Lugar y Fecha (derecha)
            
            # TABLA DE IDENTIFICACIÓN
            "ID_X":           255,              # Alineación horizontal datos
            "ID_Y_INI":       452,              # Altura primer renglón (RFC)
            "ID_SKIP":        23.5,             # Salto entre renglones

            # TABLA DE DOMICILIO
            "DOM_X1":         120,              # Columna izquierda (CP, etc)
            "DOM_X2":         430,              # Columna derecha (Vialidad, etc)
            "DOM_Y_INI":      284,              # Altura primer renglón domicilio
            "DOM_SKIP":       21.0,             # Salto entre renglones domicilio

            # --- PÁGINA 2 ---
            "QR_VALIDA":      [480, 80, 85],    # QR de la página 2
            "P2_ACTIVIDAD":   [90, 642, 7],     # Actividad Económica
            "P2_REGIMEN":     [60, 555, 7],     # Régimen Fiscal
        }
        # =========================================================

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Localización de archivos (Rutas absolutas para Vercel)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de Fuentes (Deben estar en /api)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- DIBUJO PÁGINA 1 ---
        img1 = os.path.join(base_path, '..', 'plantilla.png')
        if not os.path.exists(img1): raise FileNotFoundError(f"Falta plantilla.png en {img1}")
        c.drawImage(img1, 0, 0, width=612, height=792)

        # QRs y Textos de Cédula
        dibujar_qr(c, M["QR_CEDULA"][0], M["QR_CEDULA"][1], M["QR_CEDULA"][2], "QR_P1_TEMP")
        c.setFont("SansBold", M["CEDULA_RFC"][2])
        c.drawCentredString(M["CEDULA_RFC"][0], M["CEDULA_RFC"][1], rfc)
        c.setFont("Sans", M["CEDULA_NOM"][2])
        c.drawCentredString(M["CEDULA_NOM"][0], M["CEDULA_NOM"][1], nombre_full)

        # Fecha de Emisión
        c.setFont("SansBold", M["FECHA_EMI"][2])
        fecha_txt = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(M["FECHA_EMI"][0], M["FECHA_EMI"][1], fecha_txt)

        # Tabla Identificación (Lógica de saltos)
        c.setFont("Sans", 7)
        for i, dato in enumerate([rfc, "CURP_EJEMPLO", nombre_full, "APE1", "APE2"]):
            c.drawString(M["ID_X"], M["ID_Y_INI"] - (i * M["ID_SKIP"]), str(dato))

        # Tabla Domicilio (Ejemplos)
        c.setFont("Sans", 6.5)
        c.drawString(M["DOM_X1"], M["DOM_Y_INI"], "06700")
        c.drawString(M["DOM_X2"], M["DOM_Y_INI"], "CALZADA")

        c.showPage() # Salto de página

        # --- DIBUJO PÁGINA 2 ---
        img2 = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(img2):
            c.drawImage(img2, 0, 0, width=612, height=792)
            dibujar_qr(c, M["QR_VALIDA"][0], M["QR_VALIDA"][1], M["QR_VALIDA"][2], "QR_P2_TEMP")
            c.setFont("Sans", M["P2_ACTIVIDAD"][2])
            c.drawString(M["P2_ACTIVIDAD"][0], M["P2_ACTIVIDAD"][1], "Asalariado")

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error Crítico: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
        
