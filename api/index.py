import os, io, random, string, qrcode
from datetime import datetime
from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

app = Flask(__name__, template_folder='../templates')

def obtener_qr_img(contenido):
    qr_gen = qrcode.QRCode(box_size=10, border=0)
    qr_gen.add_data(contenido)
    qr_gen.make(fit=True)
    img = qr_gen.make_image(fill_color="black", back_color="white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def separar_nombre(nombre_full):
    p = nombre_full.split()
    if len(p) >= 3:
        return " ".join(p[:-2]), p[-2], p[-1]
    return nombre_full, "", ""

@app.route('/procesar', methods=['POST'])
def procesar():
    try:
        # --- DATOS DINÁMICOS ---
        curp = request.form.get('curp', '').upper()
        nombre_full = request.form.get('nombre', '').upper()
        rfc = curp[:10] + "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        idcif = "".join(random.choices(string.digits, k=11))
        nombres, pat, mat = separar_nombre(nombre_full)
        fecha_const = "25 DE DICIEMBRE DE 2014"
        lugar_fecha_txt = f"CIUDAD DE MÉXICO A {datetime.now().day} DE FEBRERO DE 2026"
        url_qr = f"https://{request.host}/validador?D1=10&D2=1&D3={idcif}_{rfc}"

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        base = os.path.dirname(os.path.abspath(__file__))
        
        # Registro de Fuentes
        pdfmetrics.registerFont(TTFont('Sans', os.path.join(base, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('SansBold', os.path.join(base, 'DejaVuSans-Bold.ttf')))

        # ================== PÁGINA 1 ==================
        c.drawImage(os.path.join(base, '..', 'plantilla.png'), 0, 0, width=612, height=792)

        # 1. CÉDULA SUPERIOR
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), 74, 578, width=82, height=82)
        c.setFont("SansBold", 8); c.drawCentredString(165, 638, rfc)
        c.setFont("Sans", 6.5); c.drawCentredString(165, 612, nombre_full)
        c.setFont("Sans", 6.5); c.drawCentredString(165, 595, f"idCIF: {idcif}")
        c.setFont("SansBold", 7.5); c.drawCentredString(364, 683, lugar_fecha_txt)

        # 2. IDENTIFICACIÓN DEL CONTRIBUYENTE (X=255 fijo)
        c.setFont("Sans", 7)
        c.drawString(255, 452, rfc)
        c.drawString(255, 428.5, curp)
        c.drawString(255, 405, nombres)
        c.drawString(255, 381.5, pat)
        c.drawString(255, 358, mat)
        c.drawString(255, 334.5, fecha_const)
        c.drawString(255, 311, "ACTIVO")
        c.drawString(255, 287.5, fecha_const)
        c.drawString(255, 264, " ") # Nombre comercial

        # 3. DOMICILIO FISCAL (Dos columnas)
        c.setFont("Sans", 6.5)
        # Columna Izquierda (X=120)
        c.drawString(120, 284, "06700")            # CP
        c.drawString(120, 263, "INSURGENTES")      # Nombre vialidad
        c.drawString(120, 242, "S/N")              # Num Interior
        c.drawString(120, 221, "CUAUHTÉMOC")       # Localidad
        c.drawString(120, 200, "CIUDAD DE MÉXICO") # Entidad
        # Columna Derecha (X=430)
        c.drawString(430, 284, "CALZADA")          # Tipo vialidad
        c.drawString(430, 263, "880")              # Num Exterior
        c.drawString(430, 242, "ROMA NORTE")       # Colonia
        c.drawString(430, 221, "CUAUHTÉMOC")       # Municipio
        c.drawString(430, 200, "CALLE 10 Y 12")    # Entre calle

        c.showPage()

        # ================== PÁGINA 2 ==================
        c.drawImage(os.path.join(base, '..', 'plantilla2.png'), 0, 0, width=612, height=792)
        
        # 4. ACTIVIDADES ECONÓMICAS
        c.setFont("Sans", 7)
        c.drawString(45, 615, "1")
        c.drawString(90, 615, "Asalariado")
        c.drawString(415, 615, "100")
        c.drawString(485, 615, fecha_const)

        # 5. REGÍMENES FISCALES
        c.drawString(60, 530, "Régimen de Sueldos y Salarios e Ingresos Asimilados a Salarios")
        c.drawString(485, 530, fecha_const)

        # 6. SELLOS DIGITALES (PIE)
        # Cadena Original
        c.setFont("SansBold", 6); c.drawString(60, 125, "Cadena Original Sello:")
        c.setFont("Sans", 5); c.drawString(60, 118, f"||1.1|{idcif}|{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}|{rfc}|{curp}||")
        # Sello Digital
        c.setFont("SansBold", 6); c.drawString(60, 95, "Sello Digital:")
        sello_txt = "".join(random.choices(string.ascii_letters + string.digits, k=115))
        c.setFont("Sans", 5); c.drawString(60, 88, sello_txt)
        # QR Página 2
        c.drawImage(ImageReader(obtener_qr_img(url_qr)), 480, 80, width=85, height=85)

        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'CSF_{rfc}.pdf')

    except Exception as e:
        return f"Error en generación: {str(e)}", 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validador')
def validador():
    d3 = request.args.get('D3', '')
    rfc = d3.split("_")[1] if "_" in d3 else "PERJ82100497A"
    return render_template('validador.html', d={"rfc": rfc, "situacion": "ACTIVO"})
        
