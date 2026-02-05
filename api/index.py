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

# --- CONFIGURACIÓN DE TAMAÑO (DIVIDIDO A LA MITAD) ---
# Tamaño anterior: 16 pts (equivalente al 39 de imagen). Nuevo tamaño: 8 pts.
T_BASE = 8 
T_ENCABEZADO = 10 # Un poco más grande para RFC y Nombre arriba

def generar_aleatorio(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # Datos del formulario
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Registro de fuentes (Asegúrate de tener estos archivos en la carpeta api/)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Mono', os.path.join(base_path, 'DejaVuSansMono.ttf')))

        # --- MAPEO 1: DATOS DE IDENTIFICACIÓN (PÁGINA 1) ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # Encabezado principal
        c.setFont("SansBold", T_ENCABEZADO)
        c.drawString(160, 608, rfc)
        c.setFont("Sans", T_ENCABEZADO)
        c.drawString(145, 565, nombre)

        # Tabla de Identificación (Mapeo de datos fijos)
        c.setFont("Sans", T_BASE)
        c.drawString(245, 423, rfc)      # RFC en cuadro
        c.drawString(245, 398, curp)     # CURP en cuadro
        c.drawString(245, 318, "ACTIVO") # Estatus

        # --- MAPEO 2: DATOS DEL DOMICILIO (PÁGINA 1) ---
        # Coordenadas ajustadas para los recuadros de domicilio
        c.drawString(70, 255, "52787")             # CP
        c.drawString(310, 255, "CALLE")            # Vialidad
        c.drawString(70, 235, "AVENIDA CENTRAL")   # Nombre Vialidad
        c.drawString(310, 235, "100")              # Num Exterior

        c.showPage() 

        # --- MAPEO 3: ACTIVIDADES ECONÓMICAS (PÁGINA 2) ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        c.setFont("Sans", T_BASE)
        c.drawString(50, 615, "1")           # Orden
        c.drawString(90, 615, "Asalariado")  # Actividad
        c.drawString(415, 615, "100")        # Porcentaje
        c.drawString(470, 615, "17/01/2023") # Fecha Inicio

        # --- MAPEO 4: REGÍMENES (PÁGINA 2) ---
        c.drawString(60, 528, "Régimen de sueldos y salarios e ingresos asimilados a salarios")
        c.drawString(470, 528, "17/01/2023") # Fecha Inicio Régimen

        # Sellos y Cadena (Monoespaciada)
        c.setFont("Mono", 6) # Sello aún más pequeño para máxima densidad
        cadena = f"||2026/02/04|{rfc}|CSF|{generar_aleatorio(300)}||"
        text_obj = c.beginText(122, 345)
        text_obj.setLeading(7)
        for i in range(0, len(cadena), 110): # Más caracteres por línea por fuente pequeña
            text_obj.textLine(cadena[i:i+110])
        c.drawText(text_obj)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500
        
