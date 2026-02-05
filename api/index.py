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

# --- CONFIGURACIÓN DE MAREO ---
T_GRAL = 7          
SUBIR_Y = 28        

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
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Registro de fuentes
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # =========================================================
        # PÁGINA 1
        # =========================================================
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # 1. QR de la Cédula (Página 1)
        # Ubicación aproximada según imagen de referencia
        generar_qr(c, 75, 575 + SUBIR_Y, 70, "PENDIENTE_URL_PAG1")

        # 2. Datos Identificación (Mapeo previo)
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 608 + SUBIR_Y, rfc)
        
        c.setFont("Sans", T_GRAL)
        X_DATA = 255
        Y_START = 424 + SUBIR_Y
        c.drawString(X_DATA, Y_START, rfc)
        c.drawString(X_DATA, Y_START - 23.5, curp)
        c.drawString(X_DATA, Y_START - 47.0, nombre_full)

        # 3. Fecha de Emisión
        c.setFont("SansBold", 7)
        fecha_str = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(585, 655 + SUBIR_Y, fecha_str)

        c.showPage() # Finaliza Pág 1

        # =========================================================
        # PÁGINA 2
        # =========================================================
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        # 4. QR de Validación (Página 2)
        # Ubicación al final del documento para sellos digitales
        generar_qr(c, 480, 50 + SUBIR_Y, 80, "PENDIENTE_URL_PAG2")

        # 5. Ejemplo de Actividad Económica (Página 2)
        c.setFont("Sans", T_GRAL)
        c.drawString(90, 615 + SUBIR_Y, "Asalariado")
        c.drawString(415, 615 + SUBIR_Y, "100")

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
    
