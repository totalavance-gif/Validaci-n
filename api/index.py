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

def generar_qr(c, x, y, size, data):
    """Dibuja un código QR en las coordenadas especificadas"""
    qr_code = qr.QrCodeWidget(data, barLevel='H')
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(size, size, transform=[size/width, 0, 0, size/height, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, c, x, y)

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # --- DATOS DE ENTRADA ---
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        # =========================================================
        # PANEL DE CONTROL DE COORDENADAS (AJUSTA AQUÍ)
        # =========================================================
        # Formato: "Nombre": [X, Y, Tamaño_Letra]
        # Recuerda que Y sube si el número es mayor.
        
        MAPEO = {
            # PÁGINA 1
            "P1_QR":          [75,  603, 70],  # X, Y, Tamaño del cuadro
            "P1_RFC_CEDULA":  [165, 636, 8],   # X (Centro), Y, Font
            "P1_NOM_CEDULA":  [165, 610, 6],   # X (Centro), Y, Font
            "P1_FECHA":       [585, 683, 7],   # X (Derecha), Y, Font
            "P1_TABLA_RFC":   [255, 452, 7],   # X, Y, Font
            
            # PÁGINA 2
            "P2_QR":          [480, 78,  80],  # X, Y, Tamaño del cuadro
            "P2_ACTIVIDAD":   [90,  643, 7],   # X, Y, Font
            "P2_PORCENTAJE":  [415, 643, 7]    # X, Y, Font
        }
        
        # Salto entre renglones de la tabla (Interlineado)
        LINE_SPACE = 23.5 
        # =========================================================

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Carga de fuentes
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # Dibujar QR Pág 1
        generar_qr(c, MAPEO["P1_QR"][0], MAPEO["P1_QR"][1], MAPEO["P1_QR"][2], "QR_PAGINA_1")

        # Cédula
        c.setFont("SansBold", MAPEO["P1_RFC_CEDULA"][2])
        c.drawCentredString(MAPEO["P1_RFC_CEDULA"][0], MAPEO["P1_RFC_CEDULA"][1], rfc)
        
        c.setFont("Sans", MAPEO["P1_NOM_CEDULA"][2])
        c.drawCentredString(MAPEO["P1_NOM_CEDULA"][0], MAPEO["P1_NOM_CEDULA"][1], nombre_full)

        # Fecha
        c.setFont("SansBold", MAPEO["P1_FECHA"][2])
        fecha_str = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(MAPEO["P1_FECHA"][0], MAPEO["P1_FECHA"][1], fecha_str)

        # Tabla de Identificación (Usa el LINE_SPACE para bajar automáticamente)
        c.setFont("Sans", MAPEO["P1_TABLA_RFC"][2])
        x_t, y_t = MAPEO["P1_TABLA_RFC"][0], MAPEO["P1_TABLA_RFC"][1]
        
        c.drawString(x_t, y_t, rfc)
        c.drawString(x_t, y_t - LINE_SPACE, curp)
        c.drawString(x_t, y_t - (LINE_SPACE * 2), nombre_full)

        c.showPage()

        # --- PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        # Dibujar QR Pág 2
        generar_qr(c, MAPEO["P2_QR"][0], MAPEO["P2_QR"][1], MAPEO["P2_QR"][2], "QR_PAGINA_2")

        # Actividades
        c.setFont("Sans", MAPEO["P2_ACTIVIDAD"][2])
        c.drawString(MAPEO["P2_ACTIVIDAD"][0], MAPEO["P2_ACTIVIDAD"][1], "Asalariado")
        c.drawString(MAPEO["P2_PORCENTAJE"][0], MAPEO["P2_PORCENTAJE"][1], "100")

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
        
