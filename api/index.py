import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías para PDF y QR
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, renderPDF

app = Flask(__name__, template_folder='../templates')

# --- FUNCIÓN AUXILIAR PARA QR ---
def dibujar_qr(c, x, y, tamaño, contenido):
    qr_code = qr.QrCodeWidget(contenido)
    bounds = qr_code.getBounds()
    ancho = bounds[2] - bounds[0]
    alto = bounds[3] - bounds[1]
    d = Drawing(tamaño, tamaño, transform=[tamaño/ancho, 0, 0, tamaño/alto, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, c, x, y)

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Recolección de datos
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        # =========================================================
        # PANEL DE CONTROL DE COORDENADAS (MUEVE AQUÍ X y Y)
        # =========================================================
        # [Eje_X, Eje_Y, Tamaño]
        MAPEO = {
            # PÁGINA 1
            "P1_QR":           [70,  578, 85],   # QR de la cédula
            "P1_RFC_CEDULA":   [165, 638, 8],    # RFC en el cuadro blanco
            "P1_NOM_CEDULA":   [165, 615, 6],    # Nombre en el cuadro blanco
            "P1_FECHA_EMISION":[585, 683, 7],    # Lugar y fecha (arriba der)
            "P1_TABLA_RFC":    [255, 452, 7],    # RFC en la tabla central
            
            # PÁGINA 2
            "P2_QR_VALIDA":    [480, 80, 90],    # QR de validación al final
            "P2_REGIMEN":      [60, 555, 7],     # Texto del régimen
            "P2_ACTIVIDAD":    [90, 640, 7],     # Texto de actividad
        }
        
        # Salto de línea para la tabla de identificación
        SALTO = 23.5 
        # =========================================================

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Rutas absolutas para Vercel
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de fuentes (Asegúrate que estén en la carpeta api/)
        font_path = os.path.join(base_path, 'DejaVuSans.ttf')
        font_bold_path = os.path.join(base_path, 'DejaVuSans-Bold.ttf')
        
        pdfmetrics.registerFont(TTFont('Sans', font_path))
        pdfmetrics.registerFont(TTFont('SansBold', font_bold_path))

        # --- DIBUJO PÁGINA 1 ---
        # La plantilla debe estar en la raíz, un nivel arriba de api/
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        if os.path.exists(p1_path):
            c.drawImage(p1_path, 0, 0, width=612, height=792)

        # QR Página 1 (Sin URL todavía)
        dibujar_qr(c, MAPEO["P1_QR"][0], MAPEO["P1_QR"][1], MAPEO["P1_QR"][2], "DATO_TEMPORAL_QR1")

        # Textos Cédula
        c.setFont("SansBold", MAPEO["P1_RFC_CEDULA"][2])
        c.drawCentredString(MAPEO["P1_RFC_CEDULA"][0], MAPEO["P1_RFC_CEDULA"][1], rfc)
        
        c.setFont("Sans", MAPEO["P1_NOM_CEDULA"][2])
        c.drawCentredString(MAPEO["P1_NOM_CEDULA"][0], MAPEO["P1_NOM_CEDULA"][1], nombre_full)

        # Fecha de Emisión
        c.setFont("SansBold", MAPEO["P1_FECHA_EMISION"][2])
        fecha_txt = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(MAPEO["P1_FECHA_EMISION"][0], MAPEO["P1_FECHA_EMISION"][1], fecha_txt)

        # Tabla de Identificación
        c.setFont("Sans", MAPEO["P1_TABLA_RFC"][2])
        x_t, y_t = MAPEO["P1_TABLA_RFC"][0], MAPEO["P1_TABLA_RFC"][1]
        c.drawString(x_t, y_t, rfc)
        c.drawString(x_t, y_t - SALTO, curp)
        c.drawString(x_t, y_t - (SALTO * 2), nombre_full)

        c.showPage() # Nueva página

        # --- DIBUJO PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(p2_path):
            c.drawImage(p2_path, 0, 0, width=612, height=792)

        # QR Página 2
        dibujar_qr(c, MAPEO["P2_QR_VALIDA"][0], MAPEO["P2_QR_VALIDA"][1], MAPEO["P2_QR_VALIDA"][2], "DATO_TEMPORAL_QR2")

        # Datos Página 2
        c.setFont("Sans", MAPEO["P2_ACTIVIDAD"][2])
        c.drawString(MAPEO["P2_ACTIVIDAD"][0], MAPEO["P2_ACTIVIDAD"][1], "Asalariado")
        
        c.setFont("Sans", MAPEO["P2_REGIMEN"][2])
        c.drawString(MAPEO["P2_REGIMEN"][0], MAPEO["P2_REGIMEN"][1], "Régimen de Sueldos y Salarios")

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        # Esto te ayudará a ver qué archivo falta en los logs de Vercel
        return f"Error en el servidor: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
    
