import os
import io
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS BASADAS EN IMAGEN 2550x3300 ---
COORD_RFC = (647, 575)
COORD_NOMBRE = (682, 715)
COORD_IDCIF = (880, 915)
COORD_LUGAR_FECHA = (1450, 815)
COORD_QR = (175, 680)

def procesar_imagen_servidor(datos):
    # Cargar plantilla desde la raíz
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # Cargar fuente (si no hay una .ttf en el repo, usa la básica del sistema)
    try:
        font = ImageFont.load_default(size=45)
    except:
        font = ImageFont.load_default()

    # Dibujar Textos
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font)
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font)
    draw.text(COORD_LUGAR_FECHA, f"{datos['sede']} A {datos['fecha']}", fill="black", font=font)

    # Pegar QR desde API externa
    try:
        qr_req = requests.get(datos['qr_url'], stream=True)
        if qr_req.status_code == 200:
            qr_img = Image.open(qr_req.raw).convert('RGBA')
            qr_img = qr_img.resize((410, 410)) # Ajuste según tu mapa
            img.paste(qr_img, COORD_QR, qr_img)
    except Exception as e:
        print(f"Error QR: {e}")

    # Guardar resultado
    img = img.convert('RGB')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG', quality=95)
    img_io.seek(0)
    return img_io

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generar_documento', methods=['POST'])
def generar():
    curp = request.form.get('curp', '').upper()
    nombre = request.form.get('nombre', '').upper()
    sede = request.form.get('sede', 'ADSC DISTRITO FEDERAL "1"')
    
    rfc = curp[:10]
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    fecha = datetime.now().strftime('%d/%m/%Y')
    
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=450x450&data={url_val}"

    datos = {
        'rfc': rfc, 'nombre': nombre, 'idcif': idcif,
        'sede': sede, 'fecha': fecha, 'qr_url': qr_url
    }

    img_final = procesar_imagen_servidor(datos)
    return send_file(img_final, mimetype='image/png', as_attachment=True, download_name=f"Constancia_{rfc}.png")

@app.route('/validar')
def validar():
    return render_template('validador.html', 
                           idcif=request.args.get('id'), 
                           rfc=request.args.get('rfc'), 
                           datetime=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
