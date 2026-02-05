import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE PRECISIÓN ---
T_GRAL = 7          
SUBIR_Y = 28        

def separar_nombre(nombre_completo):
    partes = nombre_completo.split()
    if len(partes) >= 3:
        paterno = partes[-2]
        materno = partes[-1]
        nombres = " ".join(partes[:-2])
    elif len(partes) == 2:
        nombres = partes[0]
        paterno = partes[1]
        materno = ""
    else:
        nombres = nombre_completo
        paterno = ""
        materno = ""
    return nombres, paterno, materno

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Registro de fuentes (Basado en tus archivos .ttf disponibles)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # PÁGINA 1
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # 1. CÉDULA (Recuadro Blanco Izquierdo)
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 610 + SUBIR_Y, rfc) # RFC centrado
        c.setFont("Sans", 6)
        c.drawCentredString(165, 580 + SUBIR_Y, nombre_full) # Nombre
        c.drawCentredString(165, 565 + SUBIR_Y, f"idCIF: {idcif}") # idCIF

        # 2. FECHA DE EMISIÓN (Derecha)
        c.setFont("SansBold", 7)
        fecha_str = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(585, 655 + SUBIR_Y, fecha_str)

        # 3. TABLA IDENTIFICACIÓN (Mapeo exacto por renglón)
        # Ajustamos X para que empiece después de la etiqueta
        X_DATA = 255
        # El primer renglón (RFC) comienza en 423 según la plantilla
        Y_START = 423 + SUBIR_Y 
        LINE_SPACE = 12.5 # Espacio exacto entre renglones de la tabla original

        c.setFont("Sans", T_GRAL)
        
        c.drawString(X_DATA, Y_START, rfc)                           # RFC
        c.drawString(X_DATA, Y_START - LINE_SPACE, curp)             # CURP
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 2), nombres)    # Nombre(s)
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 3), ape_pat)    # Primer Apellido
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 4), ape_mat)    # Segundo Apellido
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 5), "25 DE DICIEMBRE DE 2014") # Inicio Op
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 6), "ACTIVO")   # Estatus
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 7), "25 DE DICIEMBRE DE 2014") # Último Cambio
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 8), nombre_full)# Nombre Comercial

        # 4. TABLA DOMICILIO (Mapeo de cuadros inferiores)
        X_COL1 = 120 # Datos columna izquierda
        X_COL2 = 430 # Datos columna derecha
        Y_DOM = 256 + SUBIR_Y
        DOM_SPACE = 12.5

        c.setFont("Sans", 6)
        c.drawString(X_COL1, Y_DOM, "06700")                        # CP
        c.drawString(X_COL2, Y_DOM, "CALZADA")                      # Tipo Vialidad
        c.drawString(X_COL1, Y_DOM - DOM_SPACE, "INSURGENTES")      # Nombre Vialidad
        c.drawString(X_COL2, Y_DOM - DOM_SPACE, "880")              # Num Ext
        c.drawString(X_COL1, Y_DOM - (DOM_SPACE * 2), "32")         # Num Int
        c.drawString(X_COL2, Y_DOM - (DOM_SPACE * 2), "ROMA NORTE") # Colonia
        c.drawString(X_COL1, Y_DOM - (DOM_SPACE * 3), "CUAUHTÉMOC") # Localidad
        c.drawString(X_COL2, Y_DOM - (DOM_SPACE * 3), "CUAUHTÉMOC") # Municipio
        c.drawString(X_COL1, Y_DOM - (DOM_SPACE * 4), "CIUDAD DE MÉXICO") # Entidad
        c.drawString(X_COL2, Y_DOM - (DOM_SPACE * 4), "GIRASOLES")   # Entre calle

        c.showPage()
        c.save()
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
    
