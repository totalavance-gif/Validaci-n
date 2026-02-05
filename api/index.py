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
        # 1. Datos base
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)
        fecha_ini = "25 DE DICIEMBRE DE 2014"
        
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # QR Redirigible
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), 74, 578, width=82, height=82)

        # Cédula
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 638, rfc)
        c.setFont("Sans", 6)
        c.drawCentredString(165, 612, nombre_full)
        c.drawCentredString(165, 595, f"idCIF: {idcif}")

        # Identificación del Contribuyente
        c.setFont("Sans", 7)
        tx, ty, ts = 255, 452, 23.5
        c.drawString(tx, ty, rfc)
        c.drawString(tx, ty - ts, curp)
        c.drawString(tx, ty - (ts * 2), nombres)
        c.drawString(tx, ty - (ts * 3), ape_pat)
        c.drawString(tx, ty - (ts * 4), ape_mat)
        c.drawString(tx, ty - (ts * 5), fecha_ini)
        c.drawString(tx, ty - (ts * 6), "ACTIVO")
        c.drawString(tx, ty - (ts * 7), fecha_ini)

        # Domicilio Fiscal
        dx1, dx2, dy, ds = 120, 430, 284, 21.0
        c.setFont("Sans", 6.5)
        c.drawString(dx1, dy, "06700")                  # CP
        c.drawString(dx2, dy, "CALZADA")                # Tipo Vialidad
        c.drawString(dx1, dy - ds, "INSURGENTES")       # Nombre Vialidad
        c.drawString(dx2, dy - ds, "880")               # Num Ext
        c.drawString(dx1, dy - (ds * 2), "S/N")         # Num Int
        c.drawString(dx2, dy - (ds * 2), "ROMA NORTE")  # Colonia
        c.drawString(dx1, dy - (ds * 3), "CUAUHTÉMOC")  # Localidad
        c.drawString(dx2, dy - (ds * 3), "CUAUHTÉMOC")  # Municipio
        c.drawString(dx1, dy - (ds * 4), "CIUDAD DE MÉXICO") # Entidad
        c.drawString(dx2, dy - (ds * 4), "CALLE 10 Y 12")    # Entre Calle

        c.showPage()

        # --- PÁGINA 2 ---
        p2_path = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(p2_path):
            c.drawImage(p2_path, 0, 0, width=612, height=792)
            c.drawImage(ImageReader(obtener_qr_img(f"VALIDA_{rfc}")), 480, 80, width=85, height=85)
            
            c.setFont("Sans", 7)
            # Actividades y Regímenes
            c.drawString(90, 615, "Asalariado") 
            c.drawString(485, 615, fecha_ini) # Fecha Inicio Actividad
            
            c.drawString(60, 530, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
            c.drawString(485, 530, fecha_ini) # Fecha Inicio Régimen

            # Sellos Digitales
            c.setFont("Sans", 5)
            sello = "".join(random.choices(string.ascii_letters + string.digits, k=110))
            c.drawString(60, 115, "Cadena Original Sello:")
            c.drawString(60, 108, f"||1.1|{idcif}|{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}|{rfc}||")
            c.drawString(60, 85, "Sello Digital:")
            c.drawString(60, 78, sello)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validador')
def validador():
    d3 = request.args.get('D3', '')
    idcif = d3.split("_")[0] if "_" in d3 else "21030308867"
    rfc = d3.split("_")[1] if "_" in d3 else "PERJ82100497A"
    return render_template('validador.html', d={"rfc": rfc, "idcif": idcif, "situacion": "ACTIVO"})
            
