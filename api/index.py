import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías para generación de PDF profesional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

def generar_aleatorio(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Captura de datos del formulario
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        # RFC Aleatorio basado en CURP
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        # 2. Configuración del PDF en memoria
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter) # Tamaño Carta (612 x 792 pts)
        
        # Ruta base para encontrar fuentes y plantillas
        # base_path apunta a la carpeta 'api/'
        base_path = os.path.dirname(os.path.abspath(__file__))

        # 3. Registro de Fuentes TTF (Sincronizado con tus capturas de pantalla)
        # Es vital que los archivos estén dentro de la carpeta 'api/' en GitHub
        try:
            pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
            pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))
            pdfmetrics.registerFont(TTFont('Mono', os.path.join(base_path, 'DejaVuSansMono.ttf')))
        except Exception as e:
            # Si fallan, usamos fuentes estándar para no detener el proceso
            print(f"Error cargando fuentes: {e}")
            pdfmetrics.registerFont(TTFont('Sans', 'Helvetica'))
            pdfmetrics.registerFont(TTFont('SansBold', 'Helvetica-Bold'))
            pdfmetrics.registerFont(TTFont('Mono', 'Courier'))

        # --- PÁGINA 1 ---
        # La plantilla está un nivel arriba de la carpeta api/
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # TEXTO TAMAÑO "39" (En PDF usamos 16 para ese efecto visual)
        c.setFillColorRGB(0, 0, 0)
        
        # RFC y Nombre en el encabezado
        c.setFont("SansBold", 16) 
        c.drawString(160, 608, rfc)
        
        c.setFont("Sans", 16)
        c.drawString(145, 565, nombre)

        # Datos en la tabla de identificación
        c.setFont("Sans", 10)
        c.drawString(245, 423, rfc)
        c.drawString(245, 398, curp)
        c.drawString(245, 318, "ACTIVO")

        c.showPage() # Finaliza página 1 e inicia la 2

        # --- PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        # Actividades Económicas (Ajustadas para que no desaparezcan)
        c.setFont("Sans", 11)
        c.drawString(90, 614, "Asalariado") # Actividad
        c.drawString(415, 614, "100")        # Porcentaje
        
        # Regímenes
        c.setFont("Sans", 10)
        c.drawString(60, 529, "Régimen de sueldos y salarios e ingresos asimilados a salarios")

        # Sellos Digitales (Fuente Mono para densidad visual)
        c.setFont("Mono", 7)
        cadena_orig = f"||2026/02/04|{rfc}|CSF|{generar_aleatorio(300)}||"
        
        # Dibujo de cadena en bloque (Word Wrap manual para PDF)
        text_obj = c.beginText(122, 345)
        text_obj.setLeading(8) # Interlineado compacto
        for i in range(0, len(cadena_orig), 92):
            text_obj.textLine(cadena_orig[i:i+92])
        c.drawText(text_obj)

        # 4. Cierre y envío
        c.save()
        buffer.seek(0)
        
        return send_file(
            buffer, 
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'CSF_{rfc}.pdf'
        )

    except Exception as e:
        return f"Error en el servidor: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
        
