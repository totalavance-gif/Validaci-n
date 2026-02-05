import os
import io
import random
import string
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

# --- NUEVA CONFIGURACIÓN AJUSTADA ---
T_BASE = 7          # Tamaño solicitado
SUBIR = 28          # 1 cm aproximado en puntos PDF (72 pts = 1 pulgada)
T_ENCABEZADO = 8    # Proporcional para la parte superior

def generar_aleatorio(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Carga de fuentes (DejaVu Sans desde tu carpeta api/)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Mono', os.path.join(base_path, 'DejaVuSansMono.ttf')))

        # --- PÁGINA 1: IDENTIFICACIÓN Y DOMICILIO ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # Mapeo 1: Identificación (Subido 1cm)
        c.setFont("SansBold", T_ENCABEZADO)
        c.drawString(160, 608 + SUBIR, rfc)
        c.setFont("Sans", T_ENCABEZADO)
        c.drawString(145, 565 + SUBIR, nombre)

        c.setFont("Sans", T_BASE)
        c.drawString(245, 423 + SUBIR, rfc)
        c.drawString(245, 398 + SUBIR, curp)
        c.drawString(245, 318 + SUBIR, "ACTIVO")

        # Mapeo 2: Domicilio (Subido 1cm)
        c.drawString(70, 255 + SUBIR, "52787")
        c.drawString(310, 255 + SUBIR, "CALLE")
        c.drawString(70, 235 + SUBIR, "AVENIDA CENTRAL")
        c.drawString(310, 235 + SUBIR, "100")

        c.showPage() 

        # --- PÁGINA 2: ACTIVIDADES Y REGÍMENES ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        # Mapeo 3: Actividades (Subido 1cm)
        c.setFont("Sans", T_BASE)
        c.drawString(50, 615 + SUBIR, "1")
        c.drawString(90, 615 + SUBIR, "Asalariado")
        c.drawString(415, 615 + SUBIR, "100")
        c.drawString(470, 615 + SUBIR, "17/01/2023")

        # Mapeo 4: Regímenes (Subido 1cm)
        c.drawString(60, 528 + SUBIR, "Régimen de sueldos y salarios e ingresos asimilados a salarios")
        c.drawString(470, 528 + SUBIR, "17/01/2023")

        # Sellos (Ajuste de densidad para tamaño 7)
        c.setFont("Mono", 5) 
        cadena = f"||2026/02/04|{rfc}|CSF|{generar_aleatorio(350)}||"
        text_obj = c.beginText(122, 345 + SUBIR)
        text_obj.setLeading(6)
        for i in range(0, len(cadena), 130): 
            text_obj.textLine(cadena[i:i+130])
        c.drawText(text_obj)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500
        
