import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE FUENTES Y TAMAÑO ---
TAMANO_FUENTE = 39

# --- COORDENADAS BASE (EJE Y) PARA DOMICILIO ---
# Ajustadas para que el texto no "flote" y se vea natural tras los dos puntos
EJE_Y_R1 = 2256  # CP y Tipo Vialidad
EJE_Y_R2 = 2356  # Nombre Vialidad y Num Exterior
EJE_Y_R3 = 2456  # Num Interior y Colonia
EJE_Y_R4 = 2556  # Localidad y Municipio
EJE_Y_R5 = 2656  # Entidad y Entre Calle

# --- PUNTOS DE INICIO X (Donde terminan los ":" aproximadamente) ---
# Columna Izquierda
X_CP = 335
X_VIALIDAD = 425
X_INTERIOR = 365
X_LOCALIDAD = 475
X_ENTIDAD = 545

# Columna Derecha
X_TIPO_V = 1635
X_EXTERIOR = 1645
X_COLONIA = 1735
X_MUNICIPIO = 1915
X_CALLES = 1535

def procesar_imagen_servidor(datos):
    base_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    img = Image.open(base_path).convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_FUENTE)
    except:
        font = ImageFont.load_default(size=TAMANO_FUENTE)

    # --- DIBUJAR DATOS DE IDENTIFICACIÓN (Se mantienen igual) ---
    # [Aquí van tus draw.text anteriores de RFC, Nombre, etc.]

    # --- DIBUJAR DATOS DE DOMICILIO FISCAL ALINEADOS ---
    # Columna Izquierda
    draw.text((X_CP, EJE_Y_R1), "06300", fill="black", font=font)
    draw.text((X_VIALIDAD, EJE_Y_R2), "AVENIDA HIDALGO", fill="black", font=font)
    draw.text((X_INTERIOR, EJE_Y_R3), "S/N", fill="black", font=font)
    draw.text((X_LOCALIDAD, EJE_Y_R4), "CIUDAD DE MEXICO", fill="black", font=font)
    draw.text((X_ENTIDAD, EJE_Y_R5), "CIUDAD DE MEXICO", fill="black", font=font)

    # Columna Derecha
    draw.text((X_TIPO_V, EJE_Y_R1), "AVENIDA", fill="black", font=font)
    draw.text((X_EXTERIOR, EJE_Y_R2), "77", fill="black", font=font)
    draw.text((X_COLONIA, EJE_Y_R3), "GUERRERO", fill="black", font=font)
    draw.text((X_MUNICIPIO, EJE_Y_R4), "CUAUHTEMOC", fill="black", font=font)
    draw.text((X_CALLES, EJE_Y_R5), "ENTRE CALLE REFORMA Y CALLE SOTO", fill="black", font=font)

    # --- QR DE REFERENCIA ---
    draw.rectangle([(140, 596), (140+405, 596+405)], fill="black")

    img_io = io.BytesIO()
    img.convert('RGB').save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

# [Resto de las rutas de Flask se mantienen igual]
