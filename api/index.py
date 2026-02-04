import os
import io
import random
import string
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS RE-CALIBRADAS (2550x3300) ---
# RFC: +5mm a la derecha (670 + 60 = 730)
COORD_RFC = (730, 545)
COORD_NOMBRE = (635, 685)
COORD_IDCIF = (830, 895)
COORD_LUGAR_FECHA = (1370, 785)
COORD_QR = (140, 631) 

def generar_homoclave():
    # Genera 3 caracteres aleatorios para el RFC
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(3))

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # Tamaño solicitado: 39
    try:
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 39)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 39)
    except:
        font_normal = ImageFont.load_default(size=39)
        font_bold = ImageFont.load_default(size=39)

    # 1. Dibujar RFC, Nombre e idCIF
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font_normal)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font_normal)
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font_normal)
    
    # 2. Dibujar Lugar y Fecha (Único campo en NEGRITA)
    texto_lugar_fecha = f"CUAUHTEMOC, CIUDAD DE MEXICO {datos['fecha_larga']}"
    draw.text(COORD_LUGAR_FECHA, texto_lugar_fecha, fill="black", font=font_bold)

    # 3. Pegar QR
    try:
        qr_req = requests.get(datos['qr_url'], timeout=10)
        qr_img = Image.open(io.BytesIO(qr_req.content)).convert('RGBA')
        qr_img = qr_img.resize((405, 405)) 
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
    
    # RFC con Homoclave aleatoria
    rfc = curp[:10] + generar_homoclave()
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    
    # Formato: a dd de mm del aaaa
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    now = datetime.now()
    fecha_larga = f"a {now.day:02d} de {meses[now.month-1]} del {now.year}"
    
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url_val}"

    datos = {
        'rfc': rfc, 
        'nombre': nombre, 
        'idcif': idcif, 
        'fecha_larga': fecha_larga, 
        'qr_url': qr_api
    }
    
    archivo = procesar_imagen_servidor(datos)
    return send_file(archivo, mimetype='image/png', as_attachment=True, download_name=f"RFC_{rfc}.png")

@app.route('/validar')
def validar():
    return render_template('validador.html', 
                           idcif=request.args.get('id'), 
                           rfc=request.args.get('rfc'), 
                           datetime=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
