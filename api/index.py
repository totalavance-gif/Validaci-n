import fitz  # PyMuPDF
import io
import os
from flask import Flask, request, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_BASE = os.path.join(BASE_DIR, "CUPY620808MPLRRL07_LIMPIO.pdf")

@app.route("/generar", methods=["POST"])
def generar():
    # ===== DATOS =====
    nombre = request.form.get("nombre", "JUAN PEREZ")
    rfc = request.form.get("rfc", "PEPJ800101AAA")
    curp = request.form.get("curp", "PEPJ800101HDFRRN09")
    idcif = request.form.get("idcif", "21030308867")

    # ===== ABRIR PDF BASE =====
    doc = fitz.open(PDF_BASE)
    page = doc[0]

    # ===== MAPEO (AJUSTA SI QUIERES) =====
    page.insert_text(
        fitz.Point(165, 638),
        rfc,
        fontsize=8,
        fontname="helv"
    )

    page.insert_text(
        fitz.Point(165, 612),
        nombre,
        fontsize=6.5,
        fontname="helv"
    )

    page.insert_text(
        fitz.Point(165, 595),
        f"idCIF: {idcif}",
        fontsize=6.5,
        fontname="helv"
    )

    page.insert_text(
        fitz.Point(255, 452),
        curp,
        fontsize=7,
        fontname="helv"
    )

    # ===== SALIDA =====
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    doc.close()

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="CSF_GENERADA.pdf"
    )

@app.route("/")
def home():
    return "API CSF en producción"
