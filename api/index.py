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

# --- AJUSTES DE PRECISIÓN ---
# T7 es el tamaño ideal para que no choque con los bordes de la celda
T_GRAL = 7          
# El desplazamiento de 1cm (28 pts) es correcto para compensar el margen de la plantilla
SUBIR_Y = 35        

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

        # Carga de fuentes DejaVu (Asegúrate de que estén en la carpeta api/)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # PÁGINA 1
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # ---------------------------------------------------------
        # 1. CÉDULA DE IDENTIFICACIÓN FISCAL (Recuadro Blanco)
        # ---------------------------------------------------------
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 608 + SUBIR_Y, rfc)
        c.setFont("Sans", 6)
        c.drawCentredString(165, 582 + SUBIR_Y, nombre_full)
        c.drawCentredString(165, 565 + SUBIR_Y, f"idCIF: {idcif}")

        # ---------------------------------------------------------
        # 2. LUGAR Y FECHA DE EMISIÓN (Recuadro Superior Derecho)
        # ---------------------------------------------------------
        c.setFont("SansBold", 7)
        fecha_str = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(585, 655 + SUBIR_Y, fecha_str)

        # ---------------------------------------------------------
        # 3. DATOS DE IDENTIFICACIÓN (Tabla Central)
        # ---------------------------------------------------------
        # X_DATA: 255 es el inicio del texto después de la etiqueta "RFC:", "CURP:", etc.
        X_DATA = 255
        # Y_START: 424 es el punto exacto para el primer renglón (RFC)
        Y_START = 424 + SUBIR_Y 
        # LINE_SPACE: 23.5 es el espacio exacto entre renglones de la tabla original
        LINE_SPACE = 23.5 

        c.setFont("Sans", T_GRAL)
        
        c.drawString(X_DATA, Y_START, rfc)                           # Renglón RFC
        c.drawString(X_DATA, Y_START - LINE_SPACE, curp)             # Renglón CURP
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 2), nombres)    # Renglón Nombre(s)
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 3), ape_pat)    # Renglón Primer Apellido
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 4), ape_mat)    # Renglón Segundo Apellido
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 5), "25 DE DICIEMBRE DE 2014") # Inicio Op.
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 6), "ACTIVO")   # Estatus
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 7), "25 DE DICIEMBRE DE 2014") # Cambio Estado
        c.drawString(X_DATA, Y_START - (LINE_SPACE * 8), nombre_full)# Nombre Comercial

        # ---------------------------------------------------------
        # 4. DATOS DEL DOMICILIO (Tabla Inferior)
        # ---------------------------------------------------------
        # Coordenadas X para las dos columnas de la tabla de domicilio
        X_COL1 = 120 
        X_COL2 = 430 
        # Punto de inicio para Código Postal
        Y_DOM = 256 + SUBIR_Y
        DOM_SPACE = 21.0 # Salto entre renglones de domicilio

        c.setFont("Sans", 6.5)
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
        return f"Error en mapeo: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
