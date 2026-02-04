import os
import io
import random
import string
import textwrap
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- NUEVA CONFIGURACIÓN DE TAMAÑOS ---
T_GRANDE = 50   # Para RFC, Nombre, CURP (Muy legible)
T_SELLOS = 40   # Para que los sellos se vean gruesos y claros

# Coordenadas Hoja 2 (Corregidas para que aparezcan)
P2_ORDEN = (113, 611)
P2_ACTIVIDAD = (313, 613)
P2_PORCENTAJE = (1648, 612)
P2_FECHA_ACT = (1914, 610)
P2_REGIMEN = (188, 929)
P2_FECHA_REG = (1922, 929)

def gen_rand(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

def procesar_hojas(datos):
    p1 = Image.open(os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')).convert('RGB')
    p2 = Image.open(os.path.join(os.path.dirname(__file__), '..', 'plantilla2.png')).convert('RGB')
    
    try:
        f_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", T_GRANDE)
        f_reg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", T_GRANDE)
        f_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", T_SELLOS)
    except:
        f_bold = f_reg = f_mono = ImageFont.load_default()

    # --- DIBUJO HOJA 1 (Datos Principales) ---
    d1 = ImageDraw.Draw(p1)
    d1.text((730, 580), datos['rfc'], fill="black", font=f_bold)
    d1.text((635, 710), datos['nombre'], fill="black", font=f_reg)
    d1.text((957, 1246), datos['rfc'], fill="black", font=f_reg)
    d1.text((966, 1350), datos['curp'], fill="black", font=f_reg)
    # Estatus
    d1.text((989, 1810), "ACTIVO", fill="black", font=f_bold)

    # --- DIBUJO HOJA 2 (Actividad y Régimen) ---
    d2 = ImageDraw.Draw(p2)
    # Datos de la tabla (Aseguramos que aparezcan)
    d2.text(P2_ORDEN, "1", fill="black", font=f_reg)
    d2.text(P2_ACTIVIDAD, "Asalariado", fill="black", font=f_reg)
    d2.text(P2_PORCENTAJE, "100", fill="black", font=f_reg)
    d2.text(P2_FECHA_ACT, "17/01/2023", fill="black", font=f_reg)
    d2.text(P2_REGIMEN, "Régimen de sueldos y salarios e ingresos asimilados a salarios", fill="black", font=f_reg)
    d2.text(P2_FECHA_REG, "17/01/2023", fill="black", font=f_reg)

    # CADENA ORIGINAL (Bloque denso y grande)
    cad_txt = f"||2026/02/04|{datos['rfc']}|CSF|{gen_rand(220)}||"
    y_c = 1500
    # Al ser letra 40, bajamos el width a 55 para que no se salga
    for line in textwrap.wrap(cad_txt, width=55):
        d2.text((497, y_c), line, fill="black", font=f_mono)
        y_c += 50 # Salto de línea más grande para que no se encimen

    # SELLO DIGITAL
    sel_txt = gen_rand(350)
    y_s = 1700
    for line in textwrap.wrap(sel_txt, width=55):
        d2.text((487, y_s), line, fill="black", font=f_mono)
        y_s += 50

    # Fusión
    res = Image.new('RGB', (p1.width, p1.height + p2.height), (255, 255, 255))
    res.paste(p1, (0, 0))
    res.paste(p2, (0, p1.height))

    buf = io.BytesIO()
    res.save(buf, format='PNG')
    buf.seek(0)
    return buf

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + gen_rand(3).upper()
        datos = {'rfc': rfc, 'curp': curp, 'nombre': nombre}
        return send_file(procesar_hojas(datos), mimetype='image/png')
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
    
