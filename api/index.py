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

def generar_relleno(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Datos del formulario
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        # 2. Configuración del PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        # Carpeta donde vive este archivo (api/)
        base_path = os.path.dirname(__file__)

        # 3. REGISTRO DE FUENTES (Nombres exactos según tus capturas)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('Mono', os.path.join(base_path, 'DejaVuSansMono.ttf')))

        # --- PÁGINA 1 ---
        # Imagen de fondo (plantilla.png está un nivel arriba de api/)
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # CONFIGURACIÓN TAMAÑO 39
        # En PDF, 39 puntos es muy grande; si quieres que quepa en los cuadros 
        # como en el SAT original, se recomienda entre 14 y 16. 
        # Si prefieres 39 literal, usa ese número, pero podría encimarse.
        c.setFont("SansBold", 16) 
        c.drawString(160, 608, rfc)
        
        c.setFont("Sans", 16)
        c.drawString(145, 565, nombre)

        # Datos de la tabla
        c.setFont("Sans", 10)
        c.drawString(245, 423, rfc)
        c.drawString(245, 398, curp)
        c.drawString(245, 318, "ACTIVO")

        c.showPage() # Salto de página

        # --- PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        # Actividades y Regímenes
        c.setFont("Sans", 10)
        c.drawString(85, 613, "Asalariado")
        c.drawString(412, 613, "100")
        c.drawString(55, 528, "Régimen de sueldos y salarios e ingresos asimilados a salarios")

        # Bloque de Sello (Fuente Monoespaciada)
        c.setFont("Mono", 7)
        cadena = f"||2026/02/04|{rfc}|CSF|{generar_relleno(280)}||"
        text_obj = c.beginText(122, 345)
        for i in range(0, len(cadena), 95):
            text_obj.textLine(cadena[i:i+95])
        c.drawText(text_obj)

        c.save()
        buffer.seek(0)

        # Envío del PDF
        return send_file(
            buffer, 
            mimetype='application/pdf', 
            as_attachment=True, 
            download_name=f'Constancia_{rfc}.pdf'
        )

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
    
