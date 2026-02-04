import os
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Configuración robusta de rutas para Vercel
# Esto obliga a Flask a buscar 'templates' un nivel arriba de donde está este archivo
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, '..', 'templates')

app = Flask(__name__, template_folder=template_dir)

# --- DICCIONARIO DE ESTADOS Y SEDES ---
DATA_ESTADOS = {
    "AS": {"nombre": "AGUASCALIENTES", "cp": "20000", "sede": "ADSC AGUASCALIENTES \"1\""},
    "BC": {"nombre": "BAJA CALIFORNIA", "cp": "21000", "sede": "ADSC BAJA CALIFORNIA \"1\""},
    "BS": {"nombre": "BAJA CALIFORNIA SUR", "cp": "23000", "sede": "ADSC BAJA CALIFORNIA SUR \"1\""},
    "CC": {"nombre": "CAMPECHE", "cp": "24000", "sede": "ADSC CAMPECHE \"1\""},
    "CL": {"nombre": "COAHUILA", "cp": "25000", "sede": "ADSC COAHUILA \"1\""},
    "CM": {"nombre": "COLIMA", "cp": "28000", "sede": "ADSC COLIMA \"1\""},
    "CS": {"nombre": "CHIAPAS", "cp": "29000", "sede": "ADSC CHIAPAS \"1\""},
    "CH": {"nombre": "CHIHUAHUA", "cp": "31000", "sede": "ADSC CHIHUAHUA \"1\""},
    "DF": {"nombre": "CIUDAD DE MÉXICO", "cp": "06000", "sede": "ADSC DISTRITO FEDERAL \"1\""},
    "DG": {"nombre": "DURANGO", "cp": "34000", "sede": "ADSC DURANGO \"1\""},
    "GT": {"nombre": "GUANAJUATO", "cp": "37000", "sede": "ADSC GUANAJUATO \"1\""},
    "GR": {"nombre": "GUERRERO", "cp": "39000", "sede": "ADSC GUERRERO \"1\""},
    "HG": {"nombre": "HIDALGO", "cp": "42000", "sede": "ADSC HIDALGO \"1\""},
    "JC": {"nombre": "JALISCO", "cp": "44000", "sede": "ADSC JALISCO \"1\""},
    "MC": {"nombre": "MÉXICO", "cp": "50000", "sede": "ADSC MÉXICO \"1\""},
    "MN": {"nombre": "MICHOACÁN", "cp": "58000", "sede": "ADSC MICHOACÁN \"1\""},
    "MS": {"nombre": "MORELOS", "cp": "62000", "sede": "ADSC MORELOS \"1\""},
    "NT": {"nombre": "NAYARIT", "cp": "63000", "sede": "ADSC NAYARIT \"1\""},
    "NL": {"nombre": "NUEVO LEÓN", "cp": "64000", "sede": "ADSC NUEVO LEÓN \"1\""},
    "OC": {"nombre": "OAXACA", "cp": "68000", "sede": "ADSC OAXACA \"1\""},
    "PL": {"nombre": "PUEBLA", "cp": "72000", "sede": "ADSC PUEBLA \"1\""},
    "QT": {"nombre": "QUERÉTARO", "cp": "76000", "sede": "ADSC QUERÉTARO \"1\""},
    "QR": {"nombre": "QUINTANA ROO", "cp": "77000", "sede": "ADSC QUINTANA ROO \"1\""},
    "SP": {"nombre": "SAN LUIS POTOSÍ", "cp": "78000", "sede": "ADSC SAN LUIS POTOSÍ \"1\""},
    "SL": {"nombre": "SINALOA", "cp": "80000", "sede": "ADSC SINALOA \"1\""},
    "SR": {"nombre": "SONORA", "cp": "83000", "sede": "ADSC SONORA \"1\""},
    "TC": {"nombre": "TABASCO", "cp": "86000", "sede": "ADSC TABASCO \"1\""},
    "TS": {"nombre": "TAMAULIPAS", "cp": "87000", "sede": "ADSC TAMAULIPAS \"1\""},
    "TL": {"nombre": "TLAXCALA", "cp": "90000", "sede": "ADSC TLAXCALA \"1\""},
    "VZ": {"nombre": "VERACRUZ", "cp": "91000", "sede": "ADSC VERACRUZ \"1\""},
    "YN": {"nombre": "YUCATÁN", "cp": "97000", "sede": "ADSC YUCATÁN \"1\""},
    "ZS": {"nombre": "ZACATECAS", "cp": "98000", "sede": "ADSC ZACATECAS \"1\""}
}

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error: No se encontró la plantilla index.html. Detalle: {str(e)}", 500

@app.route('/generar', methods=['POST'])
def generar():
    data = request.json
    curp = data.get('curp', '').upper()
    
    # Lógica de extracción de estado
    clave_estado = curp[10:12] if len(curp) >= 12 else "DF"
    info_geo = DATA_ESTADOS.get(clave_estado, DATA_ESTADOS["DF"])
    
    # Generación de idCIF
    idcif = "".join([str(random.randint(0, 9)) for _ in range(11)])
    rfc = curp[:10]
    
    # QR apuntando a la misma URL de Vercel
    url_espejo = f"https://{request.host}/validar?id={idcif}&rfc={rfc}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={url_espejo}"

    return jsonify({
        "status": "success",
        "datos": {
            "curp": curp,
            "rfc": rfc,
            "idcif": idcif,
            "sede": data.get('sede') if data.get('sede') != 'AUTO' else info_geo['sede'],
            "fecha": data.get('fecha') or datetime.now().strftime('%d/%m/%Y'),
            "qr": qr_url,
            "cp": info_geo['cp'],
            "estado": info_geo['nombre']
        }
    })

@app.route('/validar')
def validar():
    idcif = request.args.get('id', 'N/A')
    rfc = request.args.get('rfc', 'N/A')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    return render_template('validador.html', idcif=idcif, rfc=rfc, datetime=fecha_actual)

if __name__ == '__main__':
    app.run(debug=True)
