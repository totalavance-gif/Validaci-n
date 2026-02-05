import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías para PDF y Gráficos
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing, renderPDF

app = Flask(__name__, template_folder='../templates')

def dibujar_qr(c, x, y, tamaño, contenido):
    """Genera un código QR y lo dibuja en el canvas"""
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
        # 1. Datos del Formulario
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        
        # URL de Validación Real
        url_validacion = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"

        # 2. Configuración de Coordenadas
        M = {
            "P1_QR": [74, 578, 80],
            "P2_QR": [480, 80, 85],
            "H2_Y_ACT": 615, "H2_Y_REG": 530, "H2_X_FECHA": 485,
            "X_SELLOS": 60, "Y_CADENA": 115, "Y_SELLO": 85
        }

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de fuentes
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        p1 = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1, 0, 0, width=612, height=792)
        
        # Dibujar QR con URL real de validación
        dibujar_qr(c, M["P1_QR"][0], M["P1_QR"][1], M["P1_QR"][2], url_validacion)
        
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 638, rfc)
        # ... (Resto de datos de Pág 1 que ya tienes mapeados)
        
        c.showPage()

        # --- PÁGINA 2 ---
        p2 = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2, 0, 0, width=612, height=792)
        
        # QR de Página 2 (Generalmente informativo o de validación interna)
        dibujar_qr(c, M["P2_QR"][0], M["P2_QR"][1], M["P2_QR"][2], url_validacion)

        c.setFont("Sans", 7)
        fecha_ini = "25 DE DICIEMBRE DE 2014"
        
        # Actividades y Regímenes con Fecha de Inicio
        c.drawString(90, M["H2_Y_ACT"], "Asalariado")
        c.drawString(M["H2_X_FECHA"], M["H2_Y_ACT"], fecha_ini)
        
        c.drawString(60, M["H2_Y_REG"], "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        c.drawString(M["H2_X_FECHA"], M["H2_Y_REG"], fecha_ini)

        # Cadena Original y Sello Digital
        c.setFont("Sans", 5)
        cadena = f"||1.1|{idcif}|{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}|{rfc}|{curp}||"
        sello = "".join(random.choices(string.ascii_letters + string.digits, k=120))
        
        c.drawString(M["X_SELLOS"], M["Y_CADENA"], "Cadena Original Sello:")
        c.drawString(M["X_SELLOS"], M["Y_CADENA"] - 7, cadena)
        c.drawString(M["X_SELLOS"], M["Y_SELLO"], "Sello Digital:")
        c.drawString(M["X_SELLOS"], M["Y_SELLO"] - 7, sello)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500
        
