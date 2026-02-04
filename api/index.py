import os
import io
import random
import string
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDINADAS CON AJUSTE DE +3mm HACIA ABAJO (Y + 35px) ---
# Encabezado
COORD_ENC_RFC = (730, 580)          # 545 + 35
COORD_ENC_NOMBRE = (635, 720)       # 685 + 35
COORD_ENC_IDCIF = (830, 930)        # 895 + 35
COORD_ENC_LUGAR_FECHA = (1370, 820) # 785 + 35
COORD_QR = (140, 666)               # 631 + 35

# Tabla de Identificación
TABLA_RFC = (957, 1270)             # 1235 + 35
TABLA_CURP = (966, 1350)            # 1315 + 35
TABLA_NOMBRES = (980, 1435)         # 1400 + 35
TABLA_APELLIDO1 = (977, 1525)       # 1490 + 35
TABLA_APELLIDO2 = (1008, 1620)      # 1585 + 35
TABLA_INICIO_OPS = (961, 1715)      # 1680 + 35
TABLA_ESTATUS = (989, 1810)         # 1775 + 35
TABLA_ULT_CAMBIO = (987, 1910)      # 1875 + 35

def generar_homoclave():
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(3))

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    try:
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 39)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 39)
    except:
        font_normal = ImageFont.load_default(size=39)
        font_bold = ImageFont.load_default(size=39)

    # 1. ENCABEZADO
    draw.text(COORD_ENC_RFC, datos['rfc'], fill="black", font=font_normal)
    draw.text(COORD_ENC_NOMBRE, datos['nombre_completo'], fill="black", font=font_normal)
    draw.text(COORD_ENC_IDCIF, datos['idcif'], fill="black", font=font_normal)
    draw.text(COORD_ENC_LUGAR_FECHA, f"CUAUHTEMOC, CIUDAD DE MEXICO {datos['fecha_emision_larga']}", fill="black", font=font_bold)

    # 2. TABLA
    draw.text(TABLA_RFC, datos['rfc'], fill="black", font=font_normal)
    draw.text(TABLA_CURP, datos['curp'], fill="black", font=font_normal)
    draw.text(TABLA_NOMBRES, datos['solo_nombres'], fill="black", font=font_normal)
    draw.text(TABLA_APELLIDO1, datos['apellido1'], fill="black", font=font_normal)
    draw.text(TABLA_APELLIDO2, datos['apellido2'], fill="black", font=font_normal)
    draw.text(TABLA_INICIO_OPS, datos['fecha_inicio'], fill="black", font=font_normal)
    draw.text(TABLA_ESTATUS, "ACTIVO", fill="black", font=font_normal)
    draw.text(TABLA_ULT_CAMBIO, datos['fecha_cambio'], fill="black", font=font_normal)

    # 3. QR
    try:
        qr_req = requests.get(datos['qr_url'], timeout=10)
        qr_img = Image.open(io.BytesIO(qr_req.content)).convert('RGBA')
        qr_img = qr_img.resize((405, 405)) 
        img.paste(qr_img, COORD_QR, qr_img)
    except:
        pass

    img_io = io.BytesIO()
    img.convert('RGB').save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/procesar', methods=['POST'])
def procesar():
    curp = request.form.get('curp', '').upper()
    nombre_raw = request.form.get('nombre', '').upper().split()
    
    # Desglose de nombre inteligente
    if len(nombre_raw) >= 3:
        solo_nombres = " ".join(nombre_raw[:-2])
        apellido1 = nombre_raw[-2]
        apellido2 = nombre_raw[-1]
    else:
        solo_nombres = " ".join(nombre_raw)
        apellido1 = ""
        apellido2 = ""

    rfc = curp[:10] + generar_homoclave()
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    
    # Fechas
    now = datetime.now()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_emision_larga = f"a {now.day:02d} de {meses[now.month-1]} del {now.year}"
    
    f_inicio = now - timedelta(days=365*3 + random.randint(0,30))
    f_cambio = now - timedelta(days=365 + random.randint(0,60))
    
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url_val}"

    datos = {
        'rfc': rfc, 'curp': curp, 'nombre_completo': " ".join(nombre_raw),
        'solo_nombres': solo_nombres, 'apellido1': apellido1, 'apellido2': apellido2,
        'idcif': idcif, 'fecha_emision_larga': fecha_emision_larga,
        'fecha_inicio': f_inicio.strftime('%d/%m/%Y'), 'fecha_cambio': f_cambio.strftime('%d/%m/%Y'),
        'qr_url': qr_api
    }
    
    return send_file(procesar_imagen_servidor(datos), mimetype='image/png', as_attachment=True, download_name=f"Constancia_{rfc}.png")
    
