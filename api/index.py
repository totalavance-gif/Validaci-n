import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías base para PDF (Sin dependencias complejas de gráficos)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Datos del Formulario
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))

        # =========================================================
        # PANEL DE CONTROL DE COORDENADAS (AJUSTA X y Y AQUÍ)
        # =========================================================
        M = {
            "P1_RFC_CEDULA":  [165, 638, 8],  # RFC en cuadro blanco
            "P1_NOM_CEDULA":  [165, 612, 6],  # Nombre en cuadro blanco
            "P1_FECHA_EMI":   [585, 683, 7],  # Fecha (derecha)
            "P1_TABLA_X":     255,            # Alineación datos tabla
            "P1_TABLA_Y":     452,            # Altura primer renglón
            "P1_TABLA_SKIP":  23.5,           # Salto entre renglones
        }
        # =========================================================

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Rutas absolutas para evitar errores en Vercel
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de Fuentes (Asegúrate de que estén en la carpeta /api)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        img1 = os.path.join(base_path, '..', 'plantilla.png')
        if os.path.exists(img1):
            c.drawImage(img1, 0, 0, width=612, height=792)
        else:
            return f"Error: No se encontró la imagen en {img1}", 500

        # Dibujamos textos de la Cédula
        c.setFont("SansBold", M["P1_RFC_CEDULA"][2])
        c.drawCentredString(M["P1_RFC_CEDULA"][0], M["P1_RFC_CEDULA"][1], rfc)
        c.setFont("Sans", M["P1_NOM_CEDULA"][2])
        c.drawCentredString(M["P1_NOM_CEDULA"][0], M["P1_NOM_CEDULA"][1], nombre_full)

        # Lugar y Fecha
        c.setFont("SansBold", M["P1_FECHA_EMI"][2])
        fecha_txt = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(M["P1_FECHA_EMI"][0], M["P1_FECHA_EMI"][1], fecha_txt)

        # Tabla de Identificación (Basado en tu imagen de Julio Levi)
        c.setFont("Sans", 7)
        tx, ty, skip = M["P1_TABLA_X"], M["P1_TABLA_Y"], M["P1_TABLA_SKIP"]
        c.drawString(tx, ty, rfc) # RFC
        c.drawString(tx, ty - skip, curp) # CURP
        c.drawString(tx, ty - (skip * 2), nombre_full) # Nombres

        c.showPage()

        # --- PÁGINA 2 ---
        img2 = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(img2):
            c.drawImage(img2, 0, 0, width=612, height=792)
            c.setFont("Sans", 7)
            c.drawString(90, 642, "Asalariado") # Ejemplo en Pág 2

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error detallado: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
    
