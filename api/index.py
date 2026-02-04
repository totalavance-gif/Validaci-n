import os
import io
import random
import string
import textwrap
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE TAMAÑOS ---
TAMANO_DATOS = 45   # Aumentado para máxima legibilidad
TAMANO_SELLOS = 35  # Tamaño robusto para bloques de seguridad

# Coordenadas Hoja 1
COORD_ENC_RFC = (730, 580)
COORD_ENC_NOMBRE = (635, 720)
COORD_ENC_IDCIF = (830, 884)
COORD_ENC_LUGAR_FECHA = (1370, 820)
COORD_QR_P1 = (140, 596)
# Coordenadas de tablas (Y ajustadas levemente para el nuevo tamaño)
TABLA_RFC, TABLA_CURP, TABLA_NOMBRES = (957, 1246), (966, 1350), (980, 1435)
TABLA_APELLIDO1, TABLA_APELLIDO2 = (977, 1525), (1008, 1620)
TABLA_ESTATUS = (989, 1810)

# Coordenadas Hoja 2
P2_CADENA_ORIGINAL = (497, 1500)
P2_SELLO_DIGITAL = (487, 1680)

def gen_rand(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

def procesar_hojas(datos):
    # Carga estable en RGB
    p1 = Image.open(os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')).convert('RGB')
    p2 = Image.open(os.path.join(os.path.dirname(__file__), '..', 'plantilla2.png')).convert('RGB')
    
    try:
        f_reg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_DATOS)
        f_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", TAMANO_DATOS)
        f_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", TAMANO_SELLOS)
    except:
        f_reg = f_bold = f_mono = ImageFont.load_default()

    # --- DIBUJO HOJA 1 ---
    d1 = ImageDraw.Draw(p1)
    d1.text(COORD_ENC_RFC, datos['rfc'], fill="black", font=f_bold)
    d1.text(COORD_ENC_NOMBRE, datos['nombre'], fill="black", font=f_reg)
    d1.text(COORD_ENC_IDCIF, datos['idcif'], fill="black", font=f_reg)
    d1.text(COORD_ENC_LUGAR_FECHA, datos['fecha_larga'], fill="black", font=f_bold)
    
    d1.text(TABLA_RFC, datos['rfc'], fill="black", font=f_reg)
    d1.text(TABLA_CURP, datos['curp'], fill="black", font=f_reg)
    d1.text(TABLA_NOMBRES, datos['solo_nom'], fill="black", font=f_reg)
    d1.text(TABLA_APELLIDO1, datos['ap1'], fill="black", font=f_reg)
    d1.text(TABLA_ESTATUS, "ACTIVO", fill="black", font=f_reg)
    
    # QR Hoja 1
    d1.rectangle([COORD_QR_P1, (COORD_QR_P1[0]+405, COORD_QR_P1[1]+405)], fill="black")

    # --- DIBUJO HOJA 2 ---
    d2 = ImageDraw.Draw(p2)
    
    # Cadena Original - Formato de bloque denso
    cad_text = f"||2026/02/04|{datos['rfc']}|CONSTANCIA DE SITUACION FISCAL|200001000000505|{gen_rand(280)}||"
    y_c = P2_CADENA_ORIGINAL[1]
    # Reducimos el ancho de caracteres por línea porque la letra es más grande
    for line in textwrap.wrap(cad_text, width=65):
        d2.text((P2_CADENA_ORIGINAL[0], y_c), line, fill="black", font=f_mono)
        y_c += 42 # Espaciado entre líneas

    # Sello Digital - Bloque denso
    sello_text = gen_rand(400)
    y_s = P2_SELLO_DIGITAL[1]
    for line in textwrap.wrap(sello_text, width=65):
        d2.text((P2_SELLO_DIGITAL[0], y_s), line, fill="black", font=f_mono)
        y_s += 42

    # QR Hoja 2
    d2.rectangle([(1850, 1849), (1850+524, 1849+524)], fill="black")

    # FUSIÓN DE HOJAS
    total_h = p1.height + p2.height
    resultado = Image.new('RGB', (p1.width, total_h), (255, 255, 255))
    resultado.paste(p1, (0, 0))
    resultado.paste(p2, (0, p1.height))

    img_byte_arr = io.BytesIO()
    resultado.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        partes = nombre.split()
        sn = partes[0] if partes else ""
        ap1 = partes[1] if len(partes) > 1 else ""
        
        rfc = curp[:10] + gen_rand(3).upper()
        idcif = "".join(random.choices(string.digits, k=11))
        f_larga = f"CUAUHTEMOC, CIUDAD DE MEXICO a {datetime.now().day} de febrero de 2026"

        datos = {
            'rfc': rfc, 'curp': curp, 'nombre': nombre, 'idcif': idcif,
            'solo_nom': sn, 'ap1': ap1, 'fecha_larga': f_larga
        }

        return send_file(procesar_hojas(datos), mimetype='image/png')
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
    
