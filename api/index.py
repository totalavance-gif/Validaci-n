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
TAMANO_CADENA = 28  # Aumentado
TAMANO_SELLO = 26   # Aumentado

# --- COORDENADAS PLANTILLA 1 (SIN CAMBIOS) ---
COORD_ENC_RFC = (730, 580)
COORD_ENC_NOMBRE = (635, 720)
COORD_ENC_IDCIF = (830, 884)
COORD_ENC_LUGAR_FECHA = (1370, 820)
COORD_QR_P1 = (140, 596)
TABLA_RFC, TABLA_CURP, TABLA_NOMBRES = (957, 1246), (966, 1350), (980, 1435)
TABLA_APELLIDO1, TABLA_APELLIDO2 = (977, 1525), (1008, 1620)
TABLA_INICIO_OPS, TABLA_ESTATUS, TABLA_ULT_CAMBIO = (961, 1715), (989, 1810), (987, 1910)
Y_R1, Y_R2, Y_R3, Y_R4, Y_R5 = 2244, 2344, 2444, 2532, 2632
X_CP, X_VIALIDAD, X_INTERIOR, X_LOCALIDAD, X_ENTIDAD = 342, 432, 372, 482, 540
X_TIPO_V, X_EXTERIOR, X_COLONIA, X_CALLES = 1640, 1650, 1730, 1530

# --- COORDENADAS PLANTILLA 2 ---
P2_ORDEN, P2_ACTIVIDAD, P2_PORCENTAJE = (113, 611), (313, 613), (1648, 612)
P2_FECHA_ACT, P2_REGIMEN, P2_FECHA_REG = (1914, 610), (188, 929), (1922, 929)
P2_CADENA_ORIGINAL, P2_SELLO_DIGITAL, P2_QR = (497, 1504), (487, 1656), (1850, 1849)

def generar_aleatorio(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

def procesar_hojas(datos):
    path1 = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    path2 = os.path.join(os.path.dirname(__file__), '..', 'plantilla2.png')
    
    img1 = Image.open(path1).convert('RGBA')
    img2 = Image.open(path2).convert('RGBA')
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_FUENTE)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", TAMANO_FUENTE)
        font_cadena = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", TAMANO_CADENA)
        font_sello = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", TAMANO_SELLO)
    except:
        font = ImageFont.load_default(size=TAMANO_FUENTE)
        font_b = ImageFont.load_default(size=TAMANO_FUENTE)
        font_cadena = font_sello = ImageFont.load_default(size=25)

    # --- DIBUJAR HOJA 1 ---
    d1 = ImageDraw.Draw(img1)
    d1.text(COORD_ENC_RFC, datos['rfc'], fill="black", font=font)
    d1.text(COORD_ENC_NOMBRE, datos['nombre_completo'], fill="black", font=font)
    d1.text(COORD_ENC_IDCIF, datos['idcif'], fill="black", font=font)
    d1.text(COORD_ENC_LUGAR_FECHA, f"CUAUHTEMOC, CIUDAD DE MEXICO {datos['fecha_emision_larga']}", fill="black", font=font_b)
    d1.text(TABLA_RFC, datos['rfc'], fill="black", font=font)
    d1.text(TABLA_CURP, datos['curp'], fill="black", font=font)
    d1.text(TABLA_NOMBRES, datos['solo_nombres'], fill="black", font=font)
    d1.text(TABLA_APELLIDO1, datos['apellido1'], fill="black", font=font)
    d1.text(TABLA_APELLIDO2, datos['apellido2'], fill="black", font=font)
    d1.text(TABLA_INICIO_OPS, "17/01/2023", fill="black", font=font)
    d1.text(TABLA_ESTATUS, "ACTIVO", fill="black", font=font)
    d1.text(TABLA_ULT_CAMBIO, "15/01/2025", fill="black", font=font)
    d1.text((X_CP, Y_R1), "06300", fill="black", font=font)
    d1.text((X_TIPO_V, Y_R1), "AVENIDA", fill="black", font=font)
    d1.text((X_VIALIDAD, Y_R2), "AVENIDA HIDALGO", fill="black", font=font)
    d1.text((X_EXTERIOR, Y_R2), "77", fill="black", font=font)
    d1.text((X_INTERIOR, Y_R3), "S/N", fill="black", font=font)
    d1.text((X_COLONIA, Y_R3), "GUERRERO", fill="black", font=font)
    d1.text((X_LOCALIDAD, Y_R4), "CIUDAD DE MEXICO", fill="black", font=font)
    d1.text((X_ENTIDAD, Y_R5), "CIUDAD DE MEXICO", fill="black", font=font)
    d1.text((X_CALLES, Y_R5), "ENTRE CALLE REFORMA Y CALLE SOTO", fill="black", font=font)
    d1.rectangle([COORD_QR_P1, (COORD_QR_P1[0]+405, COORD_QR_P1[1]+405)], fill="black")

    # --- DIBUJAR HOJA 2 ---
    d2 = ImageDraw.Draw(img2)
    d2.text(P2_ORDEN, "1", fill="black", font=font)
    d2.text(P2_ACTIVIDAD, "Asalariado", fill="black", font=font)
    d2.text(P2_PORCENTAJE, "100", fill="black", font=font)
    d2.text(P2_FECHA_ACT, "17/01/2023", fill="black", font=font)
    d2.text(P2_REGIMEN, "Régimen de sueldos y salarios e ingresos asimilados a salarios", fill="black", font=font)
    d2.text(P2_FECHA_REG, "17/01/2023", fill="black", font=font)

    fecha_sello = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena = f"||{fecha_sello}|{datos['rfc']}|CONSTANCIA DE SITUACION FISCAL|200001088888800351521||{generar_aleatorio(45)}|{generar_aleatorio(20)}="
    sello = f"{generar_aleatorio(90)}\n{generar_aleatorio(90)}\n{generar_aleatorio(40)}="
    
    d2.text(P2_CADENA_ORIGINAL, cadena, fill="black", font=font_cadena)
    d2.text(P2_SELLO_DIGITAL, sello, fill="black", font=font_sello)
    d2.rectangle([P2_QR, (P2_QR[0]+524, P2_QR[1]+524)], fill="black")

    # --- FUSIONAR AMBAS HOJAS EN UNA SOLA IMAGEN VERTICAL ---
    total_width = max(img1.width, img2.width)
    total_height = img1.height + img2.height
    nueva_img = Image.new('RGB', (total_width, total_height), (255, 255, 255))
    nueva_img.paste(img1, (0, 0))
    nueva_img.paste(img2, (0, img1.height))

    img_io = io.BytesIO()
    nueva_img.save(img_io, 'PNG')
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

    rfc = curp[:10] + generar_aleatorio(3)
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    now = datetime.now()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_emision_larga = f"a {now.day:02d} de {meses[now.month-1]} del {now.year}"

    datos = {
        'rfc': rfc, 'curp': curp, 'nombre_completo': " ".join(nombre_raw),
        'solo_nombres': solo_nombres, 'apellido1': apellido1, 'apellido2': apellido2,
        'idcif': idcif, 'fecha_emision_larga': fecha_emision_larga
    }
    return send_file(procesar_hojas(datos), mimetype='image/png')

@app.route('/')
def index(): return render_template('index.html')

if __name__ == '__main__': app.run(debug=True)
    
