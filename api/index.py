import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías para PDF profesional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE PRECISIÓN ---
T_BASE = 7          # Tamaño solicitado
SUBIR = 28          # 1 cm aproximado hacia arriba (28 puntos PDF)

def generar_idcif(n=11):
    return ''.join(random.choices(string.digits, k=n))

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Datos del formulario
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = generar_idcif()
        
        # 2. Preparación del PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # 3. Registro de fuentes (Rutas exactas de tu GitHub)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1: MAPEO 1 (Identificación) ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # A. SECCIÓN CÉDULA (Recuadro superior izquierdo)
        # RFC en negrita
        c.setFont("SansBold", 8) 
        c.drawCentredString(335, 608 + SUBIR, rfc)
        
        # Nombre en tamaño 7
        c.setFont("Sans", T_BASE)
        c.drawCentredString(335, 575 + SUBIR, nombre)
        
        # idCIF debajo del nombre
        c.setFont("Sans", 6)
        c.drawCentredString(335, 560 + SUBIR, f"ID CIF: {idcif}")

        # B. LUGAR Y FECHA DE EMISIÓN (Recuadro superior derecho)
        c.setFont("Sans", T_BASE)
        fecha_texto = f"CIUDAD DE MEXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(580, 655 + SUBIR, fecha_texto)

        # C. TABLA DE DATOS DE IDENTIFICACIÓN (Cuerpo central)
        # Alineación a la izquierda dentro de los campos de la tabla
        c.setFont("Sans", T_BASE)
        x_tabla = 245 # Columna de respuesta en la tabla
        
        c.drawString(x_tabla, 423 + SUBIR, rfc)      # Renglón RFC
        c.drawString(x_tabla, 398 + SUBIR, curp)     # Renglón CURP
        c.drawString(x_tabla, 373 + SUBIR, nombre)   # Renglón Nombre
        c.drawString(x_tabla, 318 + SUBIR, "ACTIVO") # Renglón Estatus

        # 4. Finalización
        c.showPage() # Solo generamos la página 1 para validar el primer mapeo
        c.save()
        buffer.seek(0)
        
        return send_file(
            buffer, 
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'CSF_{rfc}.pdf'
        )

    except Exception as e:
        return f"Error en el mapeo: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
