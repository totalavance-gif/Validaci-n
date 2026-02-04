import os
import io
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE COORDENADAS (Basadas en tu Image Map) ---
# Formato: (X, Y)
COORD_RFC = (613, 541)
COORD_NOMBRE = (647, 682)
COORD_IDCIF = (834, 879)
COORD_FECHA = (1393, 774)
COORD_QR = (170, 648) # Esquina superior izquierda del QR

def generar_imagen_constancia(datos):
    # 1. Cargar la plantilla base
    # Buscamos la imagen en la raíz del proyecto
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    
    # Crear capa para dibujar
    draw = ImageDraw.Draw(img)
    
    # 2. Cargar Fuente (Vercel usa Linux, usamos una por defecto o sube una .ttf a tu repo)
    try:
        # Si subes 'arial.ttf' a la raíz, usa esta línea:
        # font_path = os.path.join(os.path.dirname(__file__), '..', 'arial.ttf')
        # font = ImageFont.truetype(font_path, 45)
        font = ImageFont.load_default(size=40)
    except:
        font = ImageFont.load_default()

    # 3. Escribir Textos
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font)
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font)
    
    texto_full_fecha = f"{datos['sede']} A {datos['fecha']}"
    draw.text(COORD_FECHA, texto_full_fecha, fill="black", font=font)

    # 4. Descargar y Pegar el QR
    try:
        qr_response = requests.get(datos['qr_url'], stream=True)
        if qr_response.status_code == 200:
            qr_img = Image.open(qr_response.raw).convert('RGBA')
            # Ajustar tamaño del QR (según tus coordenadas 575-170 = 405px aprox)
            qr_img = qr_img.resize((400, 405)) 
            img.paste(qr_img, COORD_QR, qr_img)
    except Exception as e:
        print(f"Error pegando QR: {e}")

    # 5. Guardar en memoria para enviar al navegador
    img = img.convert('RGB') # Convertir a RGB para guardar como PNG/JPG
    img_io = io.BytesIO()
    img.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    return img_io

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    # Recibimos los datos del formulario
    curp = request.form.get('curp', '').upper()
    nombre = request.form.get('nombre', '').upper()
    sede = request.form.get('sede', 'ADSC MÉXICO "1"')
    
    # Lógica de negocio
    rfc = curp[:10]
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    fecha = datetime.now().strftime('%d/%m/%Y')
    
    # URL para el QR (Página espejo)
    url_validador = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=450x450&data={url_validador}"

    datos_finales = {
        'rfc': rfc,
        'nombre': nombre,
        'idcif': idcif,
        'sede': sede,
        'fecha': fecha,
        'qr_url': qr_url
    }

    # Generamos la imagen reconstruida
    imagen_final = generar_imagen_constancia(datos_finales)
    
    return send_file(
        imagen_final,
        mimetype='image/png',
        as_attachment=True,
        download_name=f"Constancia_{rfc}.png"
    )

@app.route('/validar')
def validar():
    idcif = request.args.get('id', 'N/A')
    rfc = request.args.get('rfc', 'N/A')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    return render_template('validador.html', idcif=idcif, rfc=rfc, datetime=fecha_actual)
    
