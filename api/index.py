import os
import io
import random
import string
import textwrap
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN DE FUENTES Y ESTILOS ---
TAMANO_FUENTE = 39
TAMANO_SELLOS = 22  # Tamaño para máxima semejanza visual

# Coordenadas Hoja 1 (Sin cambios, verificadas)
COORD_ENC_RFC = (730, 580)
COORD_ENC_NOMBRE = (635, 720)
COORD_ENC_IDCIF = (830, 884)
COORD_ENC_LUGAR_FECHA = (1370, 820)
COORD_QR_P1 = (140, 596)
TABLA_RFC, TABLA_CURP, TABLA_NOMBRES = (957, 1246), (966, 1350), (980, 1435)
TABLA_APELLIDO1, TABLA_APELLIDO2 = (977, 1525), (1008, 1620)
TABLA_INICIO_OPS, TABLA_ESTATUS, TABLA_ULT_CAMBIO = (961, 1715), (989, 1810), (987, 1910)
Y_R1, Y_R2, Y_R3, Y_R4, Y_R5 = 2244, 2344, 2444, 2532, 2632
X_CP, X_VIALIDAD, X_INTERIOR, X_LOCALIDAD, X_ENTIDAD = 342, 432, 372, 482, 540
X_TIPO_V, X_EXTERIOR, X_COLONIA, X_CALLES = 1640, 1650, 1730, 1530

# Coordenadas Hoja 2 (Tu mapeo reciente)
P2_ORDEN, P2_ACTIVIDAD, P2_PORCENTAJE = (113, 611), (313, 613), (1648, 612)
P2_FECHA_ACT, P2_REGIMEN, P2_FECHA_REG = (1914, 610), (188, 929), (1922, 929)
P2_CADENA_ORIGINAL, P2_SELLO_DIGITAL, P2_QR = (497, 1504), (487, 1656), (1850, 1849)

def generar_relleno(n):
    return ''.join(random.choice(string.ascii_letters + string.digits + "+/=") for _ in range(n))

def procesar_hojas(datos):
    # Carga de plantillas forzando modo RGB para evitar errores de transparencia
    p1_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')
    p2_path = os.path.join(os.path.dirname(__file__), '..', 'plantilla2.png')
    
    hoja1 = Image.open(p1_path).convert('RGB')
    hoja2 = Image.open(p2_path).convert('RGB')
    
    try:
        f_norm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_FUENTE)
        f_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", TAMANO_FUENTE)
        f_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", TAMANO_SELLOS)
    except:
        f_norm = f_bold = f_mono = ImageFont.load_default()

    # --- DIBUJO HOJA 1 ---
    d1 = ImageDraw.Draw(hoja1)
    d1.text(COORD_ENC_RFC, datos['rfc'], fill="black", font=f_norm)
    d1.text(COORD_ENC_NOMBRE, datos['nombre_completo'], fill="black", font=f_norm)
    d1.text(COORD_ENC_IDCIF, datos['idcif'], fill="black", font=f_norm)
    d1.text(COORD_ENC_LUGAR_FECHA, f"CUAUHTEMOC, CIUDAD DE MEXICO {datos['fecha_emision']}", fill="black", font=f_bold)
    
    # Tabla de identificación
    d1.text(TABLA_RFC, datos['rfc'], fill="black", font=f_norm)
    d1.text(TABLA_CURP, datos['curp'], fill="black", font=f_norm)
    d1.text(TABLA_NOMBRES, datos['solo_nombres'], fill="black", font=f_norm)
    d1.text(TABLA_APELLIDO1, datos['apellido1'], fill="black", font=f_norm)
    d1.text(TABLA_APELLIDO2, datos['apellido2'], fill="black", font=f_norm)
    d1.text(TABLA_INICIO_OPS, "17/01/2023", fill="black", font=f_norm)
    d1.text(TABLA_ESTATUS, "ACTIVO", fill="black", font=f_norm)
    d1.text(TABLA_ULT_CAMBIO, "15/01/2025", fill="black", font=f_norm)

    # Domicilio
    d1.text((X_CP, Y_R1), "06300", fill="black", font=f_norm)
    d1.text((X_TIPO_V, Y_R1), "AVENIDA", fill="black", font=f_norm)
    d1.text((X_VIALIDAD, Y_R2), "AVENIDA HIDALGO", fill="black", font=f_norm)
    d1.text((X_EXTERIOR, Y_R2), "77", fill="black", font=f_norm)
    d1.text((X_INTERIOR, Y_R3), "S/N", fill="black", font=f_norm)
    d1.text((X_COLONIA, Y_R3), "GUERRERO", fill="black", font=f_norm)
    d1.text((X_LOCALIDAD, Y_R4), "CIUDAD DE MEXICO", fill="black", font=f_norm)
    d1.text((X_ENTIDAD, Y_R5), "CIUDAD DE MEXICO", fill="black", font=f_norm)
    d1.text((X_CALLES, Y_R5), "ENTRE CALLE REFORMA Y CALLE SOTO", fill="black", font=f_norm)
    d1.rectangle([COORD_QR_P1, (COORD_QR_P1[0]+405, COORD_QR_P1[1]+405)], fill="black")

    # --- DIBUJO HOJA 2 ---
    d2 = ImageDraw.Draw(hoja2)
    d2.text(P2_ORDEN, "1", fill="black", font=f_norm)
    d2.text(P2_ACTIVIDAD, "Asalariado", fill="black", font=f_norm)
    d2.text(P2_PORCENTAJE, "100", fill="black", font=f_norm)
    d2.text(P2_FECHA_ACT, "17/01/2023", fill="black", font=f_norm)
    d2.text(P2_REGIMEN, "Régimen de sueldos y salarios e ingresos asimilados a salarios", fill="black", font=f_norm)
    d2.text(P2_FECHA_REG, "17/01/2023", fill="black", font=f_norm)

    # Reconstrucción Cadena Original (Asemejada al SAT)
    f_sello_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    c_base = f"||{f_sello_str}|{datos['rfc']}|CONSTANCIA DE SITUACION FISCAL|200001088888800351521||{generar_relleno(360)}||"
    y_c = P2_CADENA_ORIGINAL[1]
    for linea in textwrap.wrap(c_base, width=120):
        d2.text((P2_CADENA_ORIGINAL[0], y_c), linea, fill="black", font=f_mono)
        y_c += 26

    # Reconstrucción Sello Digital
    s_base = generar_relleno(480)
    y_s = P2_SELLO_DIGITAL[1]
    for linea in textwrap.wrap(s_base, width=120):
        d2.text((P2_SELLO_DIGITAL[0], y_s), linea, fill="black", font=f_mono)
        y_s += 26

    d2.rectangle([P2_QR, (P2_QR[0]+524, P2_QR[1]+524)], fill="black")

    # --- FUSIÓN DE AMBAS HOJAS ---
    # Creamos un lienzo nuevo basado en el ancho de la hoja 1 y el alto sumado
    lienzo = Image.new('RGB', (hoja1.width, hoja1.height + hoja2.height), (255, 255, 255))
    lienzo.paste(hoja1, (0, 0))
    lienzo.paste(hoja2, (0, hoja1.height))

    output = io.BytesIO()
    lienzo.save(output, format='PNG')
    output.seek(0)
    return output

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nombre_raw = request.form.get('nombre', '').upper().split()
        
        # Lógica de nombres
        if len(nombre_raw) >= 3:
            sn, a1, a2 = " ".join(nombre_raw[:-2]), nombre_raw[-2], nombre_raw[-1]
        else:
            sn, a1, a2 = " ".join(nombre_raw), "", ""

        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        
        m_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        f_larga = f"a {datetime.now().day:02d} de {m_es[datetime.now().month-1]} del {datetime.now().year}"

        dict_datos = {
            'rfc': rfc, 'curp': curp, 'nombre_completo': " ".join(nombre_raw),
            'solo_nombres': sn, 'apellido1': a1, 'apellido2': a2,
            'idcif': idcif, 'fecha_emision': f_larga
        }

        return send_file(procesar_hojas(dict_datos), mimetype='image/png')
    except Exception as e:
        return f"Error detectado: {str(e)}", 500

@app.route('/')
def index(): return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
