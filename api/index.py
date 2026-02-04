import os
import io
import random
import string
import textwrap # Para dividir el texto en bloques
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN GLOBAL ---
TAMANO_FUENTE = 39
TAMANO_SELLOS = 23 # Tamaño óptimo para legibilidad oficial

# --- COORDENADAS (Mantenemos tus coordenadas de mapeo) ---
# ... (Seccion de coordenadas P1 igual que antes)
P2_CADENA_ORIGINAL = (497, 1504)
P2_SELLO_DIGITAL = (487, 1656)
P2_QR = (1850, 1849)

def generar_bloque_alfanumerico(longitud):
    caracteres = string.ascii_letters + string.digits + "+/="
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def procesar_hojas(datos):
    path1 = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    path2 = os.path.join(os.path.dirname(__file__), '..', 'plantilla2.png')
    
    img1 = Image.open(path1).convert('RGBA')
    img2 = Image.open(path2).convert('RGBA')
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_FUENTE)
        # Fuente Monoespaciada es clave para los sellos
        font_sello = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", TAMANO_SELLOS)
    except:
        font = ImageFont.load_default(size=TAMANO_FUENTE)
        font_sello = ImageFont.load_default(size=TAMANO_SELLOS)

    # ... (Dibujo de Hoja 1 igual al anterior)
    d1 = ImageDraw.Draw(img1)
    # [Aquí va el código de d1 que ya tienes]

    # --- DIBUJAR HOJA 2 ---
    d2 = ImageDraw.Draw(img2)
    
    # 1. Datos de tablas (Igual que antes)
    # d2.text(P2_ORDEN, "1", ...) etc.

    # 2. CONSTRUCCIÓN VISUAL DE LA CADENA ORIGINAL
    fecha_sello = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    cadena_texto = (f"||{fecha_sello}|{datos['rfc']}|CONSTANCIA DE SITUACION FISCAL|"
                   f"200001088888800351521||{generar_bloque_alfanumerico(250)}||")
    
    # Dividir la cadena en líneas de ~120 caracteres para que parezca un bloque
    lineas_cadena = textwrap.wrap(cadena_texto, width=115)
    y_actual = P2_CADENA_ORIGINAL[1]
    for linea in lineas_cadena:
        d2.text((P2_CADENA_ORIGINAL[0], y_actual), linea, fill="black", font=font_sello)
        y_actual += 30 # Espaciado entre líneas

    # 3. CONSTRUCCIÓN VISUAL DEL SELLO DIGITAL
    # El sello digital es un bloque más compacto
    sello_texto = generar_bloque_alfanumerico(350)
    lineas_sello = textwrap.wrap(sello_texto, width=100)
    y_actual_sello = P2_SELLO_DIGITAL[1]
    for linea in lineas_sello:
        d2.text((P2_SELLO_DIGITAL[0], y_actual_sello), linea, fill="black", font=font_sello)
        y_actual_sello += 28

    # 4. QR HOJA 2
    d2.rectangle([P2_QR, (P2_QR[0]+524, P2_QR[1]+524)], fill="black")

    # --- FUSIONAR ---
    total_height = img1.height + img2.height
    nueva_img = Image.new('RGB', (img1.width, total_height), (255, 255, 255))
    nueva_img.paste(img1, (0, 0))
    nueva_img.paste(img2, (0, img1.height))

    img_io = io.BytesIO()
    nueva_img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

# ... (Resto del código de Flask igual)
