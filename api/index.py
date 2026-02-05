import fitz  # PyMuPDF
import io
import os
from flask import Flask, request, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Asegúrate de que este archivo esté en la misma carpeta que index.py
PDF_BASE = os.path.join(BASE_DIR, "CUPY620808MPLRRL07_LIMPIO.pdf")

def get_y(y_pt):
    # Altura estándar Letter es 792pt. 
    # PyMuPDF mide de arriba hacia abajo.
    return 792 - y_pt

@app.route("/generar", methods=["POST"])
def generar():
    nombre = request.form.get("nombre", "JUAN PEREZ").upper()
    rfc = request.form.get("rfc", "PEPJ800101AAA").upper()
    curp = request.form.get("curp", "PEPJ800101HDFRRN09").upper()
    idcif = request.form.get("idcif", "21030308867")

    if not os.path.exists(PDF_BASE):
        return f"Error: No se encontró el PDF base en {PDF_BASE}", 500

    doc = fitz.open(PDF_BASE)
    page = doc[0]

    # --- TEXTOS CENTRADOS (Cédula) ---
    # fitz no tiene "align center" directo en insert_text de forma sencilla,
    # pero podemos usar el parámetro 'align' en insert_textbox o calcularlo:
    
    # RFC
    page.insert_text(
        fitz.Point(165 - (len(rfc)*2), get_y(638)), # Ajuste manual de centro
        rfc,
        fontsize=8,
        fontname="helv-bold"
    )

    # Nombre
    page.insert_text(
        fitz.Point(165 - (len(nombre)*1.5), get_y(612)),
        nombre,
        fontsize=6.5,
        fontname="helv"
    )

    # idCIF
    txt_idcif = f"idCIF: {idcif}"
    page.insert_text(
        fitz.Point(165 - (len(txt_idcif)*1.5), get_y(595)),
        txt_idcif,
        fontsize=6.5,
        fontname="helv"
    )

    # --- TEXTOS ALINEADOS IZQUIERDA (Identificación) ---
    page.insert_text(
        fitz.Point(255, get_y(452)),
        rfc,
        fontsize=7,
        fontname="helv"
    )
    
    page.insert_text(
        fitz.Point(255, get_y(428.5)),
        curp,
        fontsize=7,
        fontname="helv"
    )

    # Salida
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    doc.close()

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"CSF_{rfc}.pdf"
    )

@app.route("/")
def home():
    return "Servidor PyMuPDF Activo"
    
