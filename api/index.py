import os
import io
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS PARA ALTA RESOLUCIÓN (2550x3300) ---
COORD_RFC = (620, 545)
COORD_NOMBRE = (640, 680)
COORD_IDCIF = (850, 885)
COORD_LUGAR_FECHA = (1400, 775)
COORD_QR = (170, 645)

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # TAMAÑOS GIGANTES PARA 2550px
    try:
        # Intentamos usar una fuente Bold del sistema
        font_xl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 85)
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
    except:
        # Fallback si no hay fuentes instaladas
        font_xl = ImageFont.load_default(size=90)
        font_lg = ImageFont.load_default(size=70)

    # Dibujar Textos
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font_xl)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font_xl)
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font_lg)
    
    # Sede Cuauhtémoc fija
    fecha_txt = f"CUAUHTÉMOC, CIUDAD DE MÉXICO A {datos['fecha']}"
    draw.text(COORD_LUGAR_FECHA, fecha_txt, fill="black", font=font_lg)

    # Pegar QR
    try:
        qr_req = requests.get(datos['qr_url'], timeout=10)
        qr_img = Image.open(io.BytesIO(qr_req.content)).convert('RGBA')
        qr_img = qr_img.resize((410, 410)) # Tamaño del cuadro QR
        img.paste(qr_img, COORD_QR, qr_img)
    except:
        pass

    final_img = img.convert('RGB')
    img_io = io.BytesIO()
    final_img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    curp = request.form.get('curp', '').upper()
    nombre = request.form.get('nombre', '').upper()
    
    rfc = curp[:10]
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    fecha = datetime.now().strftime('%d/%m/%Y')
    
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url_val}"

    datos = {'rfc': rfc, 'nombre': nombre, 'idcif': idcif, 'fecha': fecha, 'qr_url': qr_api}
    
    archivo = procesar_imagen_servidor(datos)
    return send_file(archivo, mimetype='image/png', as_attachment=True, download_name=f"Constancia_{rfc}.png")

@app.route('/validar')
def validar():
    return render_template('validador.html', idcif=request.args.get('id'), rfc=request.args.get('rfc'), datetime=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
