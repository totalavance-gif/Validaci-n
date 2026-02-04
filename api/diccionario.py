import random

# Mapeo de Clave CURP a Estado, CP y Oficina ADSC
DATA_ESTADOS = {
    "AS": {"nombre": "AGUASCALIENTES", "cp": "20000", "sede": "ADSC Aguascalientes \"1\""},
    "BC": {"nombre": "BAJA CALIFORNIA", "cp": "21000", "sede": "ADSC Baja California \"1\" Mexicali"},
    "BS": {"nombre": "BAJA CALIFORNIA SUR", "cp": "23000", "sede": "ADSC Baja California Sur \"1\" La Paz"},
    "CC": {"nombre": "CAMPECHE", "cp": "24000", "sede": "ADSC Campeche \"1\""},
    "CL": {"nombre": "COAHUILA", "cp": "25000", "sede": "ADSC Coahuila de Zaragoza \"1\" Saltillo"},
    "CM": {"nombre": "COLIMA", "cp": "28000", "sede": "ADSC Colima \"1\""},
    "CS": {"nombre": "CHIAPAS", "cp": "29000", "sede": "ADSC Chiapas \"1\" Tuxtla Gutiérrez"},
    "CH": {"nombre": "CHIHUAHUA", "cp": "31000", "sede": "ADSC Chihuahua \"1\""},
    "DF": {"nombre": "CIUDAD DE MÉXICO", "cp": "06000", "sede": "ADSC Distrito Federal \"1\" Centro"},
    "DG": {"nombre": "DURANGO", "cp": "34000", "sede": "ADSC Durango \"1\""},
    "GT": {"nombre": "GUANAJUATO", "cp": "37000", "sede": "ADSC Guanajuato \"1\" León"},
    "GR": {"nombre": "GUERRERO", "cp": "39000", "sede": "ADSC Guerrero \"1\" Chilpancingo"},
    "HG": {"nombre": "HIDALGO", "cp": "42000", "sede": "ADSC Hidalgo \"1\" Pachuca"},
    "JC": {"nombre": "JALISCO", "cp": "44000", "sede": "ADSC Jalisco \"1\" Guadalajara"},
    "MC": {"nombre": "MÉXICO", "cp": "50000", "sede": "ADSC México \"1\" Toluca"},
    "MN": {"nombre": "MICHOACÁN", "cp": "58000", "sede": "ADSC Michoacán \"1\" Morelia"},
    "MS": {"nombre": "MORELOS", "cp": "62000", "sede": "ADSC Morelos \"1\" Cuernavaca"},
    "NT": {"nombre": "NAYARIT", "cp": "63000", "sede": "ADSC Nayarit \"1\" Tepic"},
    "NL": {"nombre": "NUEVO LEÓN", "cp": "64000", "sede": "ADSC Nuevo León \"1\" Monterrey"},
    "OC": {"nombre": "OAXACA", "cp": "68000", "sede": "ADSC Oaxaca \"1\""},
    "PL": {"nombre": "PUEBLA", "cp": "72000", "sede": "ADSC Puebla \"1\""},
    "QT": {"nombre": "QUERÉTARO", "cp": "76000", "sede": "ADSC Querétaro \"1\""},
    "QR": {"nombre": "QUINTANA ROO", "cp": "77000", "sede": "ADSC Quintana Roo \"1\" Cancún"},
    "SP": {"nombre": "SAN LUIS POTOSÍ", "cp": "78000", "sede": "ADSC San Luis Potosí \"1\""},
    "SL": {"nombre": "SINALOA", "cp": "80000", "sede": "ADSC Sinaloa \"1\" Culiacán"},
    "SR": {"nombre": "SONORA", "cp": "83000", "sede": "ADSC Sonora \"1\" Hermosillo"},
    "TC": {"nombre": "TABASCO", "cp": "86000", "sede": "ADSC Tabasco \"1\" Villahermosa"},
    "TS": {"nombre": "TAMAULIPAS", "cp": "87000", "sede": "ADSC Tamaulipas \"1\" Victoria"},
    "TL": {"nombre": "TLAXCALA", "cp": "90000", "sede": "ADSC Tlaxcala \"1\""},
    "VZ": {"nombre": "VERACRUZ", "cp": "91000", "sede": "ADSC Veracruz \"1\" Xalapa"},
    "YN": {"nombre": "YUCATÁN", "cp": "97000", "sede": "ADSC Yucatán \"1\" Mérida"},
    "ZS": {"nombre": "ZACATECAS", "cp": "98000", "sede": "ADSC Zacatecas \"1\""}
}

def obtener_datos_estado(clave_curp):
    return DATA_ESTADOS.get(clave_curp.upper(), DATA_ESTADOS["DF"])

def generar_idcif_aleatorio():
    return "".join([str(random.randint(0, 9)) for _ in range(11)])
