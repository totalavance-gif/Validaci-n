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
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        
        buffer = io.BytesIO()
        # Tamaño carta estándar en puntos (612 x 792)
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(__file__)

        # 1. REGISTRO DE FUENTES (Usa los archivos que tienes en tu carpeta)
        # Asegúrate de que los archivos se llamen exactamente así en tu GitHub
        ruta_sans = os.path.join(base_path, 'DejaVuSans.ttf')
        ruta_bold = os.path.join(base_path, 'DejaVuSans-Bold.ttf')
        ruta_mono = os.path.join(base_path, 'DejaVuSansMono.ttf')
        
        pdfmetrics.registerFont(TTFont('Sans', ruta_sans))
        pdfmetrics.registerFont(TTFont('SansBold', ruta_bold))
        pdfmetrics.registerFont(TTFont('Mono', ruta_mono))

        # --- PÁGINA 1 ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # Texto principal en Tamaño 39 (Equivalente visual en PDF)
        c.setFont("SansBold", 14) # En PDF, 39 es gigantesco, 14-16 equivale al 39 de imagen
        c.drawString(160, 608, rfc)
        
        c.setFont("Sans", 14)
        c.drawString(145, 565, nombre)

        # Datos de la tabla
        c.setFont("Sans", 10)
        c.drawString(245, 423, rfc)
        c.drawString(245, 398, curp)
        c.drawString(245, 318, "ACTIVO")

        c.showPage() # Finaliza página 1

        # --- PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        c.drawImage(p2_path, 0, 0, width=612, height=792)

        # Actividades
        c.setFont("Sans", 10)
        c.drawString(85, 613, "Asalariado")
        c.drawString(412, 613, "100")
        
        # Régimen
        c.drawString(55, 528, "Régimen de sueldos y salarios e ingresos asimilados a salarios")

        # Sellos (Letra Monoespaciada para densidad)
        c.setFont("Mono", 7)
        cadena = f"||2026/02/04|{rfc}|CSF|{generar_relleno(280)}||"
        
        # Dibujar cadena original en bloque
        text_obj = c.beginText(122, 345)
        for i in range(0, len(cadena), 95):
            text_obj.textLine(cadena[i:i+95])
        c.drawText(text_obj)

        c.save()
        buffer.seek(0)

        # Forzar descarga como PDF
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

if __name__ == '__main__':
    app.run(debug=True)
    
