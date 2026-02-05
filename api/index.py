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

app = Flask(__name__, template_folder='../templates')

def obtener_qr_img(contenido):
    """Genera un QR usando la librería qrcode (más compatible con Vercel)"""
    qr = qrcode.QRCode(box_size=10, border=0)
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validador')
def validador():
    d3 = request.args.get('D3', '')
    idcif = d3.split("_")[0] if "_" in d3 else "23552656862"
    rfc = d3.split("_")[1] if "_" in d3 else "GOSJ960325862"
    datos = {
        "rfc": rfc, "idcif": idcif, "curp": rfc + "HDFNNL09"[:8],
        "nombre": "JULIO LEVI", "paterno": "GONZALEZ", "materno": "SANTELIZ",
        "situacion": "ACTIVO", "inicio_op": "25-12-2014"
    }
    return render_template('validador.html', d=datos)

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Datos
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)
        fecha_const = "25 DE DICIEMBRE DE 2014"
        
        # URL de validación
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Fuentes
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        img1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(img1_path, 0, 0, width=612, height=792)

        # INSERTAR QR (Convertido a imagen compatible)
        qr_img = obtener_qr_img(url_qr)
        from reportlab.lib.utils import ImageReader
        c.drawImage(ImageReader(qr_img), 74, 578, width=82, height=82)

        # Datos de texto
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 638, rfc)
        c.setFont("Sans", 7)
        tx, ty, ts = 255, 452, 23.5
        datos_id = [rfc, curp, nombres, ape_pat, ape_mat, fecha_const, "ACTIVO", fecha_const, nombre_full]
        for i, val in enumerate(datos_id):
            c.drawString(tx, ty - (i * ts), str(val))

        c.showPage()

        # --- PÁGINA 2 ---
        img2_path = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(img2_path):
            c.drawImage(img2_path, 0, 0, width=612, height=792)
            # QR Página 2 (Texto simple)
            qr_p2 = obtener_qr_img(f"VALIDACION_SAT_{rfc}")
            c.drawImage(ImageReader(qr_p2), 480, 80, width=85, height=85)
            
            c.setFont("Sans", 5)
            c.drawString(60, 115, "Cadena Original Sello:")
            c.drawString(60, 108, f"||1.1|{idcif}|{datetime.now().isoformat()}|{rfc}||")

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error Crítico: {str(e)}", 500
        
