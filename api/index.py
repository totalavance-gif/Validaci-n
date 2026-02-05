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
        # --- DATOS ---
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)
        fecha_const = "25 DE DICIEMBRE DE 2014"
        lugar_fecha = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # ================== PÁGINA 1 ==================
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # 1. QR Y CÉDULA
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), 74, 578, width=82, height=82)
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 638, rfc)
        c.setFont("Sans", 6.5)
        c.drawCentredString(165, 612, nombre_full)
        c.drawCentredString(165, 595, f"idCIF: {idcif}")

        # 2. LUGAR Y FECHA DE EMISIÓN (Corregido al recuadro superior)
        c.setFont("SansBold", 7.5)
        c.drawCentredString(728/2, 683, lugar_fecha) 

        # 3. IDENTIFICACIÓN (Tabla superior)
        c.setFont("Sans", 7)
        ix, iy, istep = 255, 452, 23.5
        datos_id = [rfc, curp, nombres, ape_pat, ape_mat, fecha_const, "ACTIVO", fecha_const, nombre_full]
        for i, val in enumerate(datos_id):
            c.drawString(ix, iy - (i * istep), str(val))

        # 4. DOMICILIO (Tabla inferior)
        dx1, dx2, dy, dstep = 120, 430, 284, 21.0
        c.setFont("Sans", 6.5)
        c.drawString(dx1, dy, "06700"); c.drawString(dx2, dy, "CALZADA")
        c.drawString(dx1, dy-dstep, "INSURGENTES"); c.drawString(dx2, dy-dstep, "880")
        c.drawString(dx1, dy-(dstep*2), "S/N"); c.drawString(dx2, dy-(dstep*2), "ROMA NORTE")
        c.drawString(dx1, dy-(dstep*3), "CUAUHTÉMOC"); c.drawString(dx2, dy-(dstep*3), "CUAUHTÉMOC")
        c.drawString(dx1, dy-(dstep*4), "CIUDAD DE MÉXICO"); c.drawString(dx2, dy-(dstep*4), "CALLE 10 Y 12")

        c.showPage()

        # ================== PÁGINA 2 ==================
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(p2_path):
            c.drawImage(p2_path, 0, 0, width=612, height=792)
            
            # 5. ACTIVIDADES ECONÓMICAS (Dentro de celdas)
            c.setFont("Sans", 7)
            c.drawString(45, 615, "1")                # Orden
            c.drawString(90, 615, "Asalariado")        # Actividad
            c.drawString(415, 615, "100")              # Porcentaje
            c.drawString(485, 615, fecha_const)        # Fecha Inicio

            # 6. REGÍMENES (Dentro de celdas)
            c.drawString(60, 530, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
            c.drawString(485, 530, fecha_const)        # Fecha Inicio

            # 7. SELLOS Y CADENA (Pie de página)
            c.setFont("SansBold", 6)
            c.drawString(60, 125, "Cadena Original Sello:")
            c.setFont("Sans", 5)
            c.drawString(60, 118, f"||1.1|{idcif}|{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}|{rfc}|{curp}||")
            
            c.setFont("SansBold", 6)
            c.drawString(60, 95, "Sello Digital:")
            c.setFont("Sans", 5)
            sello_fake = "".join(random.choices(string.ascii_letters + string.digits, k=110))
            c.drawString(60, 88, sello_fake)

            # 8. QR VALIDACIÓN P2
            c.drawImage(ImageReader(obtener_qr_img(url_qr)), 480, 80, width=85, height=85)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index(): return render_template('index.html')

@app.route('/validador')
def validador():
    d3 = request.args.get('D3', '')
    rfc = d3.split("_")[1] if "_" in d3 else "PERJ82100497A"
    return render_template('validador.html', d={"rfc": rfc, "situacion": "ACTIVO"})
      
