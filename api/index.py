import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS DE MAPEO ---
# Encabezado (Ajustados 3mm arriba)
COORD_ENC_RFC = (730, 580)
COORD_ENC_NOMBRE = (635, 720)
COORD_ENC_IDCIF = (830, 860)        # Subido 3mm
COORD_ENC_LUGAR_FECHA = (1370, 820)
COORD_QR_POS = (140, 596)           # Subido 3mm

# Tabla de Identificación (Tal cual la dejaste)
TABLA_RFC = (957, 1246) 
TABLA_CURP = (966, 1350)
TABLA_NOMBRES = (980, 1435)
TABLA_APELLIDO1 = (977, 1525)
TABLA_APELLIDO2 = (1008, 1620)
TABLA_INICIO_OPS = (961, 1715)
TABLA_ESTATUS = (989, 1810)
TABLA_ULT_CAMBIO = (987, 1910)

def generar_homoclave():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

def procesar_imagen_servidor(datos):
    # Cargar plantilla
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # Cargar fuentes
    try:
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 39)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 39)
    except:
        font_normal = ImageFont.load_default()
        font_bold = ImageFont.load_default()

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

    # 3. QR (CUADRO NEGRO TEMPORAL PARA MAPEO)
    # Dibujamos un cuadro negro donde irá el QR para validar posición
    draw.rectangle([COORD_QR_POS, (COORD_QR_POS[0]+405, COORD_QR_POS[1]+405)], fill="black")

    img_io = io.BytesIO()
    img.convert('RGB').save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/procesar', methods=['POST'])
def procesar():
    curp = request.form.get('curp', '').upper()
    nombre_raw = request.form.get('nombre', '').upper().split()
    
    if len(nombre_raw) >= 3:
        solo_nombres = " ".join(nombre_raw[:-2])
        apellido1 = nombre_raw[-2]
        apellido2 = nombre_raw[-1]
    else:
        solo_nombres = " ".join(nombre_raw)
        apellido1 = ""; apellido2 = ""

    rfc = curp[:10] + generar_homoclave()
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    
    now = datetime.now()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_emision_larga = f"a {now.day:02d} de {meses[now.month-1]} del {now.year}"

    datos = {
        'rfc': rfc, 'curp': curp, 'nombre_completo': " ".join(nombre_raw),
        'solo_nombres': solo_nombres, 'apellido1': apellido1, 'apellido2': apellido2,
        'idcif': idcif, 'fecha_emision_larga': fecha_emision_larga,
        'fecha_inicio': "17/01/2023", 'fecha_cambio': "15/01/2025"
    }
    
    return send_file(procesar_imagen_servidor(datos), mimetype='image/png', as_attachment=True, download_name=f"Mapeo_{rfc}.png")

@app.route('/')
def index():
    return render_template('index.html')
    
