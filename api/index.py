import fitz  # PyMuPDF
import io
import os
from flask import Flask, request, send_file, render_template

app = Flask(__name__, template_folder='../templates')

# Helper de coordenadas (ReportLab -> PyMuPDF)
def get_y(y_pt):
    return 792 - y_pt

@app.route("/procesar", methods=["POST"])
def procesar():
    doc = None
    try:
        # 1. Datos del formulario
        nombre = request.form.get("nombre", "JUAN PEREZ").upper()
        curp = request.form.get("curp", "PEPJ800101HDFRRN09").upper()
        rfc = request.form.get("rfc", curp[:13]).upper()
        idcif = request.form.get("idcif", "21030308867")

        # 2. Ruta LOCAL (Ya que el PDF está dentro de /api junto a este archivo)
        base_path = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(base_path, "CUPY620808MPLRRL07_LIMPIO.pdf")

        if not os.path.exists(pdf_path):
            return f"Error: Archivo no encontrado en {pdf_path}. Verifica que el nombre sea idéntico.", 404

        # 3. Abrir y Mapear
        doc = fitz.open(pdf_path)
        page = doc[0]

        # Estilo de fuente estándar de PDF (Helvetica)
        f_bold = "helv-bold"
        f_reg = "helv"

        # --- Bloque Cédula ---
        page.insert_text(fitz.Point(165 - (len(rfc)*2), get_y(638)), rfc, fontsize=8, fontname=f_bold)
        page.insert_text(fitz.Point(165 - (len(nombre)*1.5), get_y(612)), nombre, fontsize=6.5, fontname=f_reg)
        page.insert_text(fitz.Point(165 - (len(f"idCIF: {idcif}")*1.5), get_y(595)), f"idCIF: {idcif}", fontsize=6.5, fontname=f_reg)

        # --- Bloque Identificación ---
        page.insert_text(fitz.Point(255, get_y(452)), rfc, fontsize=7, fontname=f_reg)
        page.insert_text(fitz.Point(255, get_y(428.5)), curp, fontsize=7, fontname=f_reg)
        page.insert_text(fitz.Point(255, get_y(405)), nombre, fontsize=7, fontname=f_reg)

        # 4. Enviar resultado
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"CSF_{rfc}.pdf"
        )

    except Exception as e:
        return f"Ocurrió un error: {str(e)}", 500
    finally:
        if doc:
            doc.close()

@app.route("/")
def home():
    return render_template("index.html")
        
