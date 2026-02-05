import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías base para PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

def separar_nombre(nombre_completo):
    """Separa el nombre para llenar los renglones de la tabla central"""
    partes = nombre_completo.split()
    if len(partes) >= 3:
        paterno = partes[-2]
        materno = partes[-1]
        nombres = " ".join(partes[:-2])
    elif len(partes) == 2:
        nombres, paterno, materno = partes[0], partes[1], ""
    else:
        nombres, paterno, materno = nombre_completo, "", ""
    return nombres, paterno, materno

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # 1. Datos del Formulario
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)

        # =========================================================
        # PANEL DE CONTROL DE COORDENADAS (AJUSTA X e Y AQUÍ)
        # =========================================================
        M = {
            # CÉDULA (Cuadro Blanco)
            "C_RFC": [165, 638, 8], "C_NOM": [165, 612, 6], "C_ID": [165, 595, 6],
            # FECHA
            "FECHA": [585, 683, 7],
            # TABLA IDENTIFICACIÓN
            "ID_X": 255, "ID_Y": 452, "ID_SKIP": 23.5,
            # TABLA DOMICILIO
            "D_X1": 120, "D_X2": 430, "D_Y": 284, "D_SKIP": 21.0,
            # HOJA 2
            "H2_ACT": [90, 642], "H2_REG": [60, 555]
        }
        # =========================================================

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de Fuentes
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- PÁGINA 1 ---
        img1 = os.path.join(base_path, '..', 'plantilla.png')
        if os.path.exists(img1):
            c.drawImage(img1, 0, 0, width=612, height=792)

        # Rellenar Cédula
        c.setFont("SansBold", M["C_RFC"][2])
        c.drawCentredString(M["C_RFC"][0], M["C_RFC"][1], rfc)
        c.setFont("Sans", M["C_NOM"][2])
        c.drawCentredString(M["C_NOM"][0], M["C_NOM"][1], nombre_full)
        c.drawCentredString(M["C_ID"][0], M["C_ID"][1], f"idCIF: {idcif}")

        # Fecha de Emisión
        c.setFont("SansBold", M["FECHA"][2])
        fecha_txt = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(M["FECHA"][0], M["FECHA"][1], fecha_txt)

        # Tabla de Identificación (Basado en imagen de referencia)
        c.setFont("Sans", 7)
        tx, ty, ts = M["ID_X"], M["ID_Y"], M["ID_SKIP"]
        c.drawString(tx, ty, rfc)                       # RFC
        c.drawString(tx, ty - ts, curp)                 # CURP
        c.drawString(tx, ty - (ts * 2), nombres)        # Nombre(s)
        c.drawString(tx, ty - (ts * 3), ape_pat)        # Primer Apellido
        c.drawString(tx, ty - (ts * 4), ape_mat)        # Segundo Apellido
        c.drawString(tx, ty - (ts * 5), "25 DE DICIEMBRE DE 2014") # Fecha Inicio
        c.drawString(tx, ty - (ts * 6), "ACTIVO")       # Estatus
        c.drawString(tx, ty - (ts * 7), "25 DE DICIEMBRE DE 2014") # Fecha Cambio
        c.drawString(tx, ty - (ts * 8), nombre_full)    # Nombre Comercial

        # Tabla de Domicilio
        c.setFont("Sans", 6.5)
        dx1, dx2, dy, ds = M["D_X1"], M["D_X2"], M["D_Y"], M["D_SKIP"]
        c.drawString(dx1, dy, "06700")                  # CP
        c.drawString(dx2, dy, "CALZADA")                # Tipo Vialidad
        c.drawString(dx1, dy - ds, "INSURGENTES")       # Nombre Vialidad
        c.drawString(dx2, dy - ds, "880")               # Num Ext
        c.drawString(dx1, dy - (ds * 2), "32")          # Num Int
        c.drawString(dx2, dy - (ds * 2), "ROMA NORTE")  # Colonia
        c.drawString(dx1, dy - (ds * 3), "CUAUHTÉMOC")  # Localidad
        c.drawString(dx2, dy - (ds * 3), "CUAUHTÉMOC")  # Municipio
        c.drawString(dx1, dy - (ds * 4), "CIUDAD DE MÉXICO") # Entidad
        c.drawString(dx2, dy - (ds * 4), "GIRASOLES")    # Entre Calle

        c.showPage() # Fin Hoja 1

        # --- PÁGINA 2 ---
        img2 = os.path.join(base_path, '..', 'plantilla2.png')
        if os.path.exists(img2):
            c.drawImage(img2, 0, 0, width=612, height=792)
            c.setFont("Sans", 7)
            c.drawString(M["H2_ACT"][0], M["H2_ACT"][1], "Asalariado") # Actividad
            c.drawString(415, M["H2_ACT"][1], "100") # Porcentaje
            c.drawString(M["H2_REG"][0], M["H2_REG"][1], "Régimen de Sueldos y Salarios") # Régimen

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')
      
