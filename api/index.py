import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN GLOBAL ---
TAMANO_FUENTE = 39

# --- COORDENADAS: IDENTIFICACIÓN ---
COORD_ENC_RFC = (730, 580)
COORD_ENC_NOMBRE = (635, 720)
COORD_ENC_IDCIF = (830, 884)
COORD_ENC_LUGAR_FECHA = (1370, 820)
COORD_QR_POS = (140, 596)

TABLA_RFC = (957, 1246) 
TABLA_CURP = (966, 1350)
TABLA_NOMBRES = (980, 1435)
TABLA_APELLIDO1 = (977, 1525)
TABLA_APELLIDO2 = (1008, 1620)
TABLA_INICIO_OPS = (961, 1715)
TABLA_ESTATUS = (989, 1810)
TABLA_ULT_CAMBIO = (987, 1910)

# --- COORDENADAS: DOMICILIO FISCAL ---
# Filas Y
Y_R1 = 2244  # CP y Tipo Vialidad
Y_R2 = 2344  # Vialidad y Num Ext
Y_R3 = 2444  # Num Int y Colonia
Y_R4 = 2532  # Localidad (Municipio eliminado de aquí)
Y_R5 = 2632  # Entidad y Calles

# Columna Izquierda (X)
X_CP = 342          
X_VIALIDAD = 432    
X_INTERIOR = 372    
X_LOCALIDAD = 482   
X_ENTIDAD = 540     

# Columna Derecha (X)
X_TIPO_V = 1640     
X_EXTERIOR = 1650   
X_COLONIA = 1730    
X_CALLES = 1530     

def generar_homoclave():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    try:
        # Intentar cargar fuentes estándar de Linux (Vercel)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_FUENTE)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", TAMANO_FUENTE)
    except:
        font = ImageFont.load_default(size=TAMANO_FUENTE)
        font_b = ImageFont.load_default(size=TAMANO_FUENTE)

    # 1. DIBUJAR IDENTIFICACIÓN
    draw.text(COORD_ENC_RFC, datos['rfc'], fill="black", font=font)
    draw.text(COORD_ENC_NOMBRE, datos['nombre_completo'], fill="black", font=font)
    draw.text(COORD_ENC_IDCIF, datos['idcif'], fill="black", font=font)
    draw.text(COORD_ENC_LUGAR_FECHA, f"CUAUHTEMOC, CIUDAD DE MEXICO {datos['fecha_emision_larga']}", fill="black", font=font_b)
    
    draw.text(TABLA_RFC, datos['rfc'], fill="black", font=font)
    draw.text(TABLA_CURP, datos['curp'], fill="black", font=font)
    draw.text(TABLA_NOMBRES, datos['solo_nombres'], fill="black", font=font)
    draw.text(TABLA_APELLIDO1, datos['apellido1'], fill="black", font=font)
    draw.text(TABLA_APELLIDO2, datos['apellido2'], fill="black", font=font)
    draw.text(TABLA_INICIO_OPS, datos['fecha_inicio'], fill="black", font=font)
    draw.text(TABLA_ESTATUS, "ACTIVO", fill="black", font=font)
    draw.text(TABLA_ULT_CAMBIO, datos['fecha_cambio'], fill="black", font=font)

    # 2. DIBUJAR DOMICILIO (Municipio removido)
    draw.text((X_CP, Y_R1), "06300", fill="black", font=font)
    draw.text((X_TIPO_V, Y_R1), "AVENIDA", fill="black", font=font)
    draw.text((X_VIALIDAD, Y_R2), "AVENIDA HIDALGO", fill="black", font=font)
    draw.text((X_EXTERIOR, Y_R2), "77", fill="black", font=font)
    draw.text((X_INTERIOR, Y_R3), "S/N", fill="black", font=font)
    draw.text((X_COLONIA, Y_R3), "GUERRERO", fill="black", font=font)
    draw.text((X_LOCALIDAD, Y_R4), "CIUDAD DE MEXICO", fill="black", font=font)
    draw.text((X_ENTIDAD, Y_R5), "CIUDAD DE MEXICO", fill="black", font=font)
    draw.text((X_CALLES, Y_R5), "ENTRE CALLE REFORMA Y CALLE SOTO", fill="black", font=font)

    # 3. REFERENCIA QR
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
        solo_nombres, apellido1, apellido2 = " ".join(nombre_raw[:-2]), nombre_raw[-2], nombre_raw[-1]
    else:
        solo_nombres, apellido1, apellido2 = " ".join(nombre_raw), "", ""

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
    
    return send_file(procesar_imagen_servidor(datos), mimetype='image/png', as_attachment=False, download_name=f"CIF_{rfc}.png")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
