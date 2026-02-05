import os
import io
import random
import string
import qrcode
from datetime import datetime
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

app = Flask(__name__, template_folder='../templates')

def obtener_qr_img(contenido):
    qr_gen = qrcode.QRCode(box_size=10, border=0)
    qr_gen.add_data(contenido)
    qr_gen.make(fit=True)
    img = qr_gen.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def separar_nombre(nombre_completo):
    partes = nombre_completo.split()
    if len(partes) >= 3:
        paterno, materno, nombres = partes[-2], partes[-1], " ".join(partes[:-2])
    elif len(partes) == 2:
        nombres, paterno, materno = partes[0], partes[1], ""
    else:
        nombres, paterno, materno = nombre_completo, "", ""
    return nombres, paterno, materno

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)
        fecha_ini = "25 DE DICIEMBRE DE 2014"
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # 1. QR y Datos de Cédula
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), 74, 578, width=82, height=82)
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 638, rfc)
        c.setFont("Sans", 6.5)
        c.drawCentredString(165, 612, nombre_full)
        
        # 2. Lugar y Fecha de Emisión (NUEVO)
        c.setFont("SansBold", 7.5)
        c.drawRightString(585, 683, lugar_fecha) 
        c.setFont("Sans", 7)
        c.drawCentredString(725/2, 245, lugar_fecha) # Texto pequeño bajo el cuadro

        # 3. Tabla Identificación
        ix, iy, istep = 255, 452, 23.5
        datos_id = [rfc, curp, nombres, ape_pat, ape_mat, fecha_ini, "ACTIVO", fecha_ini, nombre_full]
        for i, val in enumerate(datos_id):
            c.drawString(ix, iy - (i * istep), str(val))

        # 4. Tabla Domicilio
        dx1, dx2, dy, ds = 120, 430, 284, 21.0
        c.setFont("Sans", 6.5)
        c.drawString(dx1, dy, "06700"); c.drawString(dx2, dy, "CALZADA")
        c.drawString(dx1, dy-ds, "INSURGENTES"); c.drawString(dx2, dy-ds, "880")
        c.drawString(dx1, dy-(ds*2), "S/N"); c.drawString(dx2, dy-(ds*2), "ROMA NORTE")
        c.drawString(dx1, dy-(ds*3), "CUAUHTÉMOC"); c.drawString(dx2, dy-(ds*3), "CUAUHTÉMOC")
        c.drawString(dx1, dy-(ds*4), "CIUDAD DE MÉXICO"); c.drawString(dx2, dy-(ds*4), "GIRASOLES")

        c.showPage()

        # --- PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(p2_path):
            c.drawImage(p2_path, 0, 0, width=612, height=792)
            
            # 1. ACTIVIDADES ECONÓMICAS
            c.setFont("Sans", 7)
            c.drawString(45, 615, "1") # Orden
            c.drawString(90, 615, "Asalariado") # Actividad
            c.drawString(415, 615, "100") # Porcentaje
            c.drawString(485, 615, fecha_ini) # Fecha Inicio

            # 2. REGÍMENES
            c.drawString(60, 530, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
            c.drawString(485, 530, fecha_ini) # Fecha Inicio Régimen

            # 3. CADENA Y SELLOS (Ubicación Inferior)
            c.setFont("SansBold", 6)
            c.drawString(60, 125, "Cadena Original Sello:")
            c.setFont("Sans", 5)
            cadena = f"||1.1|{idcif}|{datetime.now().isoformat()}|{rfc}|{curp}||"
            c.drawString(60, 118, cadena)
            
            c.setFont("SansBold", 6)
            c.drawString(60, 95, "Sello Digital:")
            c.setFont("Sans", 5)
            sello = "".join(random.choices(string.ascii_letters + string.digits, k=115))
            c.drawString(60, 88, sello)

            # 4. QR DE VALIDACIÓN P2
            c.drawImage(ImageReader(obtener_qr_img(url_qr)), 480, 80, width=85, height=85)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index(): return render_template('index.html')
    
