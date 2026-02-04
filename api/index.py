import os
import io
import random
import string
import textwrap
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE TAMAÑOS (AHORA SÍ FUNCIONALES) ---
T_DATOS = 50   # Tamaño grande para máxima legibilidad
T_SELLOS = 38  # Tamaño para bloque compacto de seguridad

def generar_aleatorio(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

def procesar_hojas(datos):
    # Rutas base
    base_path = os.path.dirname(__file__)
    
    # Carga de Plantillas
    p1 = Image.open(os.path.join(base_path, '..', 'plantilla.png')).convert('RGB')
    p2 = Image.open(os.path.join(base_path, '..', 'plantilla2.png')).convert('RGB')
    
    # Carga de Fuentes Locales (Las que descargaste)
    try:
        f_reg = ImageFont.truetype(os.path.join(base_path, 'DejaVuSans.ttf'), T_DATOS)
        f_bold = ImageFont.truetype(os.path.join(base_path, 'DejaVuSans-Bold.ttf'), T_DATOS)
        f_mono = ImageFont.truetype(os.path.join(base_path, 'DejaVuSansMono.ttf'), T_SELLOS)
    except:
        # Si fallan los archivos, se usa el default (pero se verá pequeño)
        f_reg = f_bold = f_mono = ImageFont.load_default()

    # --- DIBUJO HOJA 1 ---
    d1 = ImageDraw.Draw(p1)
    # Encabezado
    d1.text((730, 580), datos['rfc'], fill="black", font=f_bold)
    d1.text((635, 710), datos['nombre'], fill="black", font=f_reg)
    d1.text((830, 884), datos['idcif'], fill="black", font=f_reg)
    d1.text((1370, 820), datos['fecha_emision'], fill="black", font=f_bold)
    
    # Tabla Identificación (Tamaño 50)
    d1.text((957, 1246), datos['rfc'], fill="black", font=f_reg)
    d1.text((966, 1350), datos['curp'], fill="black", font=f_reg)
    d1.text((989, 1810), "ACTIVO", fill="black", font=f_bold)
    
    # QR P1
    d1.rectangle([(140, 596), (140+405, 596+405)], fill="black")

    # --- DIBUJO HOJA 2 ---
    d2 = ImageDraw.Draw(p2)
    
    # Actividades y Regímenes (Coordenadas ajustadas para tamaño 50)
    d2.text((113, 608), "1", fill="black", font=f_reg)
    d2.text((313, 608), "Asalariado", fill="black", font=f_reg)
    d2.text((1648, 608), "100", fill="black", font=f_reg)
    d2.text((188, 925), "Régimen de sueldos y salarios e ingresos asimilados a salarios", fill="black", font=f_reg)
    d2.text((1922, 925), "17/01/2023", fill="black", font=f_reg)

    # Cadena Original (Formato denso con DejaVuSansMono)
    cadena = f"||2026/02/04|{datos['rfc']}|CONSTANCIA DE SITUACION FISCAL|200001000000505|{generar_aleatorio(250)}||"
    y_c = 1500
    for line in textwrap.wrap(cadena, width=60):
        d2.text((497, y_c), line, fill="black", font=f_mono)
        y_c += 42 # Interlineado para bloque sólido

    # Sello Digital
    sello = generar_aleatorio(380)
    y_s = 1685
    for line in textwrap.wrap(sello, width=60):
        d2.text((487, y_s), line, fill="black", font=f_mono)
        y_s += 42

    # QR P2
    d2.rectangle([(1850, 1849), (1850+524, 1849+524)], fill="black")

    # --- FUSIÓN DE PÁGINAS ---
    resultado = Image.new('RGB', (p1.width, p1.height + p2.height), (255, 255, 255))
    resultado.paste(p1, (0, 0))
    resultado.paste(p2, (0, p1.height))

    img_io = io.BytesIO()
    resultado.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        
        # Fecha de emisión dinámica
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        hoy = datetime.now()
        f_larga = f"a {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

        datos_dict = {
            'rfc': rfc, 'curp': curp, 'nombre': nombre, 
            'idcif': idcif, 'fecha_emision': f_larga
        }
        
        return send_file(procesar_hojas(datos_dict), mimetype='image/png')
    except Exception as e:
        return f"Error en el servidor: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    
