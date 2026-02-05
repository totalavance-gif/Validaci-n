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

# --- FUNCIÓN PARA DIBUJAR QR ---
def dibujar_qr(c, x, y, size, data):
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
        # PANEL DE CONTROL DE COORDENADAS (AJUSTA AQUÍ)
        # Formato: [Eje_X, Eje_Y, Tamaño_Fuente/Cuadro]
        # =========================================================
        M = {
            # PÁGINA 1
            "P1_QR_CEDULA":   [74,  578, 80],   # QR en la cédula
            "P1_RFC_CEDULA":  [165, 638, 8],    # RFC arriba (centrado)
            "P1_NOM_CEDULA":  [165, 612, 6],    # Nombre arriba (centrado)
            "P1_ID_CEDULA":   [165, 595, 6],    # idCIF arriba (centrado)
            "P1_FECHA_EMI":   [585, 683, 7],    # Lugar y Fecha (der)
            
            # TABLA IDENTIFICACIÓN
            "P1_TABLA_X":     255,              # Alineación horizontal de datos
            "P1_TABLA_Y":     452,              # Altura del primer renglón (RFC)
            "P1_TABLA_SKIP":  23.5,             # Salto entre renglones (LINE_SPACE)

            # TABLA DOMICILIO (PÁGINA 1 ABAJO)
            "P1_DOM_X_COL1":  120,              # Columna 1 (CP, Vialidad...)
            "P1_DOM_X_COL2":  430,              # Columna 2 (Tipo, NumExt...)
            "P1_DOM_Y":       284,              # Altura primer renglón domicilio
            "P1_DOM_SKIP":    21.0,             # Salto entre renglones domicilio

            # PÁGINA 2
            "P2_QR_VALIDA":   [480, 80, 85],    # QR de validación final
            "P2_ACTIVIDAD":   [90, 642, 7],     # Actividad económica
            "P2_REGIMEN":     [60, 555, 7],     # Régimen fiscal
        }
        # =========================================================

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Rutas de Archivos para evitar Error 500 en Vercel
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de Fuentes (Deben estar en la carpeta /api)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        img1 = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(img1, 0, 0, width=612, height=792)

        # QR Cédula
        dibujar_qr(c, M["P1_QR_CEDULA"][0], M["P1_QR_CEDULA"][1], M["P1_QR_CEDULA"][2], "DATO_QR_1")

        # Textos Cédula
        c.setFont("SansBold", M["P1_RFC_CEDULA"][2])
        c.drawCentredString(M["P1_RFC_CEDULA"][0], M["P1_RFC_CEDULA"][1], rfc)
        c.setFont("Sans", M["P1_NOM_CEDULA"][2])
        c.drawCentredString(M["P1_NOM_CEDULA"][0], M["P1_NOM_CEDULA"][1], nombre_full)
        c.drawCentredString(M["P1_ID_CEDULA"][0], M["P1_ID_CEDULA"][1], f"idCIF: {idcif}")

        # Lugar y Fecha
        c.setFont("SansBold", M["P1_FECHA_EMI"][2])
        fecha_full = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(M["P1_FECHA_EMI"][0], M["P1_FECHA_EMI"][1], fecha_full)

        # Identificación (Lógica de saltos automáticos)
        c.setFont("Sans", 7)
        tx, ty, skip = M["P1_TABLA_X"], M["P1_TABLA_Y"], M["P1_TABLA_SKIP"]
        c.drawString(tx, ty, rfc)
        c.drawString(tx, ty - skip, curp)
        c.drawString(tx, ty - (skip * 2), nombre_full) # Simplificado a Nombre Full

        # Domicilio (Lógica de dos columnas)
        c.setFont("Sans", 6.5)
        dx1, dx2, dy, dskip = M["P1_DOM_X_COL1"], M["P1_DOM_X_COL2"], M["P1_DOM_Y"], M["P1_DOM_SKIP"]
        c.drawString(dx1, dy, "06700")            # CP
        c.drawString(dx2, dy, "CALZADA")          # Tipo Vialidad
        c.drawString(dx1, dy - dskip, "INSURGENTES") # Nombre Vialidad
        c.drawString(dx2, dy - dskip, "880")      # Num Ext

        c.showPage()

        # --- PÁGINA 2 ---
        img2 = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(img2, 0, 0, width=612, height=792)

        # QR Página 2
        dibujar_qr(c, M["P2_QR_VALIDA"][0], M["P2_QR_VALIDA"][1], M["P2_QR_VALIDA"][2], "DATO_QR_2")

        # Datos Página 2
        c.setFont("Sans", M["P2_ACTIVIDAD"][2])
        c.drawString(M["P2_ACTIVIDAD"][0], M["P2_ACTIVIDAD"][1], "Asalariado")
        c.setFont("Sans", M["P2_REGIMEN"][2])
        c.drawString(M["P2_REGIMEN"][0], M["P2_REGIMEN"][1], "Régimen de Sueldos y Salarios")

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error detallado: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
    
