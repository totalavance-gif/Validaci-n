import os
import io
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- COORDENADAS RE-ALINEADAS PARA TAMAÑO 45 ---
COORD_RFC = (635, 545)
COORD_NOMBRE = (635, 685)
COORD_IDCIF = (830, 895)
COORD_LUGAR_FECHA = (1370, 785) # Movido a la izquierda para que no se corte
COORD_QR = (175, 655)

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # --- TAMAÑO SOLICITADO: 45 ---
    try:
        # Intentamos cargar la fuente estándar de Vercel (DejaVuSans)
        # El tamaño 45 es ideal para que quepa en los recuadros sin chocar
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
    except:
        # Fallback si el servidor no tiene la fuente instalada
        font_main = ImageFont.load_default(size=45)
        font_sm = ImageFont.load_default(size=38)

    # Dibujar Textos
    # RFC y Nombre en Negritas (font_main)
    draw.text(COORD_RFC, datos['rfc'], fill="black", font=font_main)
    draw.text(COORD_NOMBRE, datos['nombre'], fill="black", font=font_main)
    
    # idCIF y Fecha en tamaño estándar
    draw.text(COORD_IDCIF, datos['idcif'], fill="black", font=font_sm)
    
    # Texto de Sede (Sin acento complejo para evitar errores de símbolos)
    fecha_txt = f"CUAUHTEMOC, CIUDAD DE MEXICO A {datos['fecha']}"
    draw.text(COORD_LUGAR_FECHA, fecha_txt, fill="black", font=font_sm)

    # Pegar QR
    try:
        qr_req = requests.get(datos['qr_url'], timeout=10)
        qr_img = Image.open(io.BytesIO(qr_req.content)).convert('RGBA')
        qr_img = qr_img.resize((405, 405)) 
        img.paste(qr_img, COORD_QR, qr_img)
    except:
        pass

    # Finalizar imagen
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
    
    # Generar QR dinámico
    url_val = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url_val}"

    datos = {'rfc': rfc, 'nombre': nombre, 'idcif': idcif, 'fecha': fecha, 'qr_url': qr_api}
    
    archivo = procesar_imagen_servidor(datos)
    return send_file(archivo, mimetype='image/png', as_attachment=True, download_name=f"Constancia_{rfc}.png")

@app.route('/validar')
def validar():
    return render_template('validador.html', 
                           idcif=request.args.get('id'), 
                           rfc=request.args.get('rfc'), 
                           datetime=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
