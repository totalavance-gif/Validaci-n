import os
import io
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS PARA IMAGEN 2550x3300 (Ajustadas según tu mapa) ---
# Usamos los centros aproximados de tus áreas de coordenadas
COORD_RFC = (613, 545)
COORD_NOMBRE = (647, 685)
COORD_IDCIF = (834, 885)
COORD_LUGAR_FECHA = (1400, 780)
COORD_QR = (170, 648) 

def procesar_imagen_servidor(datos):
    # Cargar plantilla
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # Intentar cargar fuente, si falla usa la de sistema
    try:
        # En Vercel no siempre hay fuentes instaladas, intentamos la estándar de Linux
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
    except:
        font = ImageFont.load_default()

    # Dibujar Textos
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font)
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font)
    
    fecha_txt = f"{datos['sede']} A {datos['fecha']}"
    draw.text(COORD_LUGAR_FECHA, fecha_txt, fill="black", font=font)

    # Pegar QR
    try:
        qr_req = requests.get(datos['qr_url'], timeout=5)
        qr_img = Image.open(io.BytesIO(qr_req.content)).convert('RGBA')
        # Redimensionar QR para que encaje (405x367 según tus coordenadas)
        qr_img = qr_img.resize((405, 367))
        img.paste(qr_img, COORD_QR, qr_img)
    except Exception as e:
        print(f"Error QR: {e}")

    # Convertir a RGB y enviar
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
    sede = request.form.get('sede', 'ADSC DISTRITO FEDERAL "1"')
    
    rfc = curp[:10]
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    fecha = datetime.now().strftime('%d/%m/%Y')
    
    # URL de validación para el QR
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=450x450&data={url_val}"

    datos = {
        'rfc': rfc, 'nombre': nombre, 'idcif': idcif,
        'sede': sede, 'fecha': fecha, 'qr_url': qr_api
    }

    archivo_procesado = procesar_imagen_servidor(datos)
    return send_file(archivo_procesado, mimetype='image/png', as_attachment=True, download_name=f"RFC_{rfc}.png")

@app.route('/validar')
def validar():
    return render_template('validador.html', 
                           idcif=request.args.get('id'), 
                           rfc=request.args.get('rfc'), 
                           datetime=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        
