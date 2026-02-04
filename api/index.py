import os
import io
import random
import string
import textwrap
from datetime import datetime
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder='../templates')

# --- CONFIGURACIÓN TOTAL A 39 ---
TAMANO_FIXED = 39

# Coordenadas (Mapeo verificado)
COORD_ENC_RFC = (730, 580); COORD_ENC_NOMBRE = (635, 720); COORD_ENC_IDCIF = (830, 884)
COORD_ENC_LUGAR_FECHA = (1370, 820); COORD_QR_P1 = (140, 596)
TAB_RFC, TAB_CURP, TAB_NOM = (957, 1246), (966, 1350), (980, 1435)
TAB_AP1, TAB_AP2 = (977, 1525), (1008, 1620)
TAB_INI, TAB_EST, TAB_ULT = (961, 1715), (989, 1810), (987, 1910)
Y_R1, Y_R2, Y_R3, Y_R4, Y_R5 = 2244, 2344, 2444, 2532, 2632
X_CP, X_VIAL, X_INT, X_LOC, X_ENT = 342, 432, 372, 482, 540
X_TV, X_EXT, X_COL, X_CAL = 1640, 1650, 1730, 1530
P2_ORD, P2_ACT, P2_POR = (113, 611), (313, 613), (1648, 612)
P2_F_A, P2_REG, P2_F_R = (1914, 610), (188, 929), (1922, 929)
P2_CAD, P2_SEL, P2_QR = (497, 1504), (487, 1656), (1850, 1849)

def gen_txt(n):
    return ''.join(random.choices(string.ascii_letters + string.digits + "+/=", k=n))

def procesar_hojas(datos):
    # Carga forzada en modo RGB (fondo blanco) para evitar errores de PNG
    p1 = Image.open(os.path.join(os.path.dirname(__file__), '..', 'plantilla.png')).convert('RGB')
    p2 = Image.open(os.path.join(os.path.dirname(__file__), '..', 'plantilla2.png')).convert('RGB')
    
    try:
        f_n = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", TAMANO_FIXED)
        f_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", TAMANO_FIXED)
        f_m = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", TAMANO_FIXED)
    except:
        f_n = f_b = f_m = ImageFont.load_default()

    # --- HOJA 1 ---
    d1 = ImageDraw.Draw(p1)
    d1.text(COORD_ENC_RFC, datos['rfc'], fill="black", font=f_n)
    d1.text(COORD_ENC_NOMBRE, datos['nom_full'], fill="black", font=f_n)
    d1.text(COORD_ENC_IDCIF, datos['idcif'], fill="black", font=f_n)
    d1.text(COORD_ENC_LUGAR_FECHA, f"MEXICO {datos['f_e']}", fill="black", font=f_b)
    d1.text(TAB_RFC, datos['rfc'], fill="black", font=f_n)
    d1.text(TAB_CURP, datos['curp'], fill="black", font=f_n)
    d1.text(TAB_NOM, datos['sn'], fill="black", font=f_n)
    d1.text(TAB_AP1, datos['a1'], fill="black", font=f_n)
    d1.text(TAB_AP2, datos['a2'], fill="black", font=f_n)
    d1.text(TAB_INI, "17/01/2023", fill="black", font=f_n)
    d1.text(TAB_EST, "ACTIVO", fill="black", font=f_n)
    d1.text(TAB_ULT, "15/01/2025", fill="black", font=f_n)
    # Domicilio a 39
    d1.text((X_CP, Y_R1), "06300", fill="black", font=f_n)
    d1.text((X_TV, Y_R1), "AVENIDA", fill="black", font=f_n)
    d1.text((X_VIAL, Y_R2), "AVENIDA HIDALGO", fill="black", font=f_n)
    d1.text((X_EXT, Y_R2), "77", fill="black", font=f_n)
    d1.text((X_COL, Y_R3), "GUERRERO", fill="black", font=f_n)
    d1.rectangle([COORD_QR_P1, (COORD_QR_P1[0]+405, COORD_QR_P1[1]+405)], fill="black")

    # --- HOJA 2 ---
    d2 = ImageDraw.Draw(p2)
    d2.text(P2_ORD, "1", fill="black", font=f_n)
    d2.text(P2_ACT, "Asalariado", fill="black", font=f_n)
    d2.text(P2_POR, "100", fill="black", font=f_n)
    d2.text(P2_F_A, "17/01/2023", fill="black", font=f_n)
    d2.text(P2_REG, "Régimen de sueldos y salarios e ingresos asimilados", fill="black", font=f_n)
    d2.text(P2_F_R, "17/01/2023", fill="black", font=f_n)

    # CADENA Y SELLO (A 39 PAREJO)
    cad = f"||{datetime.now().strftime('%Y/%m/%d')}|{datos['rfc']}|CSF|{gen_txt(180)}||"
    y_c = P2_CAD[1]
    # Con letra 39, solo caben aprox 60 caracteres por línea
    for l in textwrap.wrap(cad, width=60):
        d2.text((P2_CAD[0], y_c), l, fill="black", font=f_m)
        y_c += 48 # Salto de línea amplio para evitar encime

    sel = gen_txt(240)
    y_s = P2_SEL[1]
    for l in textwrap.wrap(sel, width=60):
        d2.text((P2_SEL[0], y_s), l, fill="black", font=f_m)
        y_s += 48

    d2.rectangle([P2_QR, (P2_QR[0]+524, P2_QR[1]+524)], fill="black")

    # FUSIÓN ESTABLE (RGB)
    res = Image.new('RGB', (p1.width, p1.height + p2.height), (255, 255, 255))
    res.paste(p1, (0, 0))
    res.paste(p2, (0, p1.height))

    buf = io.BytesIO()
    res.save(buf, format='PNG')
    buf.seek(0)
    return buf

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        curp = request.form.get('curp', '').upper()
        nom = request.form.get('nombre', '').upper().split()
        sn, a1, a2 = (" ".join(nom[:-2]), nom[-2], nom[-1]) if len(nom) >= 3 else (" ".join(nom), "", "")
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        m = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        now = datetime.now()
        f_l = f"a {now.day:02d} de {m[now.month-1]} del {now.year}"
        
        datos = {'rfc': rfc, 'curp': curp, 'nom_full': " ".join(nom), 'sn': sn, 'a1': a1, 'a2': a2, 'idcif': "".join(random.choices(string.digits, k=11)), 'f_e': f_l}
        
        return send_file(procesar_hojas(datos), mimetype='image/png')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/')
def index(): return render_template('index.html')

if __name__ == '__main__': app.run(debug=True)
    
