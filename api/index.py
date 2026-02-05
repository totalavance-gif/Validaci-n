import os
import io
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, send_file

# Librerías para PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN IDÉNTICA AL ORIGINAL ---
T_GRAL = 7          # Tamaño solicitado
T_BOLD = 8          # Un poco más grande para RFC en Cédula
SUBIR_Y = 28        # Ajuste vertical (1cm) para cuadrar con tu plantilla

def separar_nombre(nombre_completo):
    """Separa el nombre en: Nombres, Paterno, Materno para llenar la tabla"""
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
        # 1. Datos del formulario
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        
        # Generamos RFC y ID-CIF
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        
        # Separamos el nombre para que llene los renglones como en la foto
        nombres, ape_pat, ape_mat = separar_nombre(nombre_full)

        # 2. Lienzo PDF
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base_path = os.path.dirname(os.path.abspath(__file__))

        # 3. Fuentes (Rutas exactas)
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base_path, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base_path, 'DejaVuSans-Bold.ttf')))

        # --- DIBUJO DE PÁGINA 1 ---
        p1_path = os.path.join(base_path, '..', 'plantilla.png')
        c.drawImage(p1_path, 0, 0, width=612, height=792)

        # ---------------------------------------------------------
        # SECCIÓN 1: CÉDULA DE IDENTIFICACIÓN FISCAL (Arriba Izq)
        # ---------------------------------------------------------
        # Coordenadas calculadas visualmente de 1000038237.jpg
        # Centro aproximado del recuadro blanco: X=165
        
        c.setFont("SansBold", 8)
        c.drawCentredString(165, 638 + SUBIR_Y, rfc) # RFC Arriba
        
        c.setFont("Sans", 6) # Nombre en la cédula es muy pequeño
        c.drawCentredString(165, 615 + SUBIR_Y, nombre_full) 
        
        c.setFont("Sans", 6)
        c.drawCentredString(165, 595 + SUBIR_Y, f"idCIF: {idcif}")

        # ---------------------------------------------------------
        # SECCIÓN 2: LUGAR Y FECHA (Arriba Derecha)
        # ---------------------------------------------------------
        c.setFont("SansBold", 7)
        # Texto alineado a la derecha, terminando en X=585
        fecha_str = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        c.drawRightString(585, 655 + SUBIR_Y, fecha_str)

        # ---------------------------------------------------------
        # SECCIÓN 3: TABLA DE DATOS DE IDENTIFICACIÓN (Centro)
        # ---------------------------------------------------------
        # En la imagen original, los valores empiezan aprox en X=255
        # El interlineado (espacio entre renglones) es de aprox 20-22 puntos.
        
        X_VAL = 255
        Y_INI = 535 + SUBIR_Y # Altura del primer renglón (RFC)
        STEP = 24            # Salto entre renglones calculado de la imagen

        c.setFont("Sans", T_GRAL)
        
        # 1. RFC
        c.drawString(X_VAL, Y_INI, rfc)
        
        # 2. CURP
        c.drawString(X_VAL, Y_INI - STEP, curp)
        
        # 3. Nombre(s)
        c.drawString(X_VAL, Y_INI - (STEP * 2), nombres)
        
        # 4. Primer Apellido
        c.drawString(X_VAL, Y_INI - (STEP * 3), ape_pat)
        
        # 5. Segundo Apellido
        c.drawString(X_VAL, Y_INI - (STEP * 4), ape_mat)
        
        # 6. Fecha inicio de operaciones
        c.drawString(X_VAL, Y_INI - (STEP * 5), "25 DE DICIEMBRE DE 2014")
        
        # 7. Estatus en el padrón
        c.drawString(X_VAL, Y_INI - (STEP * 6), "ACTIVO")
        
        # 8. Fecha de último cambio
        c.drawString(X_VAL, Y_INI - (STEP * 7), "25 DE DICIEMBRE DE 2014")
        
        # 9. Nombre Comercial
        c.drawString(X_VAL, Y_INI - (STEP * 8), nombre_full)

        # ---------------------------------------------------------
        # SECCIÓN 4: DATOS DEL DOMICILIO (Abajo)
        # ---------------------------------------------------------
        # Columna Izquierda (X ~ 150) y Columna Derecha (X ~ 430)
        # Y empieza aprox en 315
        
        Y_DOM = 315 + SUBIR_Y
        STEP_DOM = 20
        
        c.setFont("Sans", 6) # Domicilio suele ser letra un poco más chica
        
        # Renglón 1: CP y Tipo Vialidad
        c.drawString(120, Y_DOM, "06700")
        c.drawString(430, Y_DOM, "CALZADA")
        
        # Renglón 2: Vialidad y Num Ext
        c.drawString(120, Y_DOM - STEP_DOM, "INSURGENTES")
        c.drawString(430, Y_DOM - STEP_DOM, "880")
        
        # Renglón 3: Num Int y Colonia
        c.drawString(120, Y_DOM - (STEP_DOM * 2), "32")
        c.drawString(430, Y_DOM - (STEP_DOM * 2), "ROMA NORTE")
        
        # Renglón 4: Localidad y Municipio
        c.drawString(120, Y_DOM - (STEP_DOM * 3), "CUAUHTÉMOC")
        c.drawString(430, Y_DOM - (STEP_DOM * 3), "CUAUHTÉMOC")

        # Renglón 5: Entidad y Entre Calle
        c.drawString(120, Y_DOM - (STEP_DOM * 4), "CIUDAD DE MÉXICO")
        c.drawString(430, Y_DOM - (STEP_DOM * 4), "GIRASOLES")

        c.showPage()
        c.save()
        buffer.seek(0)
        
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
        
