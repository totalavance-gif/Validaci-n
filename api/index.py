import os
import io
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS RECALIBRADAS (Imagen 2550x3300) ---
COORD_RFC = (640, 565)           # Un poco más arriba para letra grande
COORD_NOMBRE = (680, 705)
COORD_IDCIF = (880, 905)
COORD_LUGAR_FECHA = (1450, 805)
COORD_QR = (175, 680)

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # --- TAMAÑO DE LETRA AUMENTADO ---
    # Intentamos cargar una fuente bold si está disponible, si no, aumentamos la escala
    try:
        # En Vercel, cargamos una fuente del sistema con tamaño grande (70-80 para RFC/Nombre)
        font_principal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        font_datos = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_fecha = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
    except:
        # Fallback si no encuentra la fuente específica
        font_principal = ImageFont.load_default(size=80)
        font_datos = ImageFont.load_default(size=65)
        font_fecha = ImageFont.load_default(size=50)

    # Dibujar con los nuevos tamaños
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font_principal)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font_principal)
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font_datos)
    
    texto_full_fecha = f"{datos['sede']} A {datos['fecha']}"
    draw.text(COORD_LUGAR_FECHA, texto_full_fecha, fill="black", font=font_fecha)

    # Pegar QR
    try:
        qr_req = requests.get(datos['qr_url'], stream=True)
        qr_img = Image.open(qr_req.raw).convert('RGBA')
        qr_img = qr_img.resize((410, 410)) 
        img.paste(qr_img, COORD_QR, qr_img)
    except:
        pass

    img = img.convert('RGB')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    return img_io

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar_documento', methods=['POST'])
def generar():
    curp = request.form.get('curp', '').upper()
    nombre = request.form.get('nombre', '').upper()
    
    # --- SEDE POR DEFAULT: CUAUHTÉMOC ---
    sede = "CUAUHTÉMOC, CIUDAD DE MÉXICO"
    
    rfc = curp[:10]
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    fecha = datetime.now().strftime('%d/%m/%Y')
    
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url_val}"

    datos = {
        'rfc': rfc, 'nombre': nombre, 'idcif': idcif,
        'sede': sede, 'fecha': fecha, 'qr_url': qr_url
    }

    img_final = procesar_imagen_servidor(datos)
    return send_file(img_final, mimetype='image/png', as_attachment=True, download_name=f"Constancia_{rfc}.png")
    
