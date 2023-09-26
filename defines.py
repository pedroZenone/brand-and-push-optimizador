APP_PORT = 5501
P_WEIGHT = 0.8
P_VOLUMEN = 0.8
P_PRICE = 0.1
W_DELAY = 1  # Castigo para los que paquetes que van quedando viejos

output_columns = ["id_run","id_item", "cod_prod", "folio", "numdpc", "placa", "id_vehiculo", "name_vehiculo", "price_warn",
                  "grupo","precio_grupo", "precio_vehiculo", "propiedad","sucursal","poblacion","volumen","peso"]

output_table_format = {
    "id_run": lambda x: int(x),
    "id_item": lambda x: int(x),
    "cod_prod": lambda x: "'" + str(x) + "'",
    "folio": lambda x: "'" + str(x) + "'",
    "numdpc": lambda x: "'" + str(x) + "'",
    "grupo": lambda x: "'" + str(x) + "'",
    "placa": lambda x: "'" + str(x) + "'",
    "id_vehiculo": lambda x: "'" + str(x) + "'",
    "name_vehiculo": lambda x: "'" + str(x) + "'",
    "price_warn": lambda x: int(x),
    "precio_grupo": lambda x: round(x,2),
    "precio_vehiculo": lambda x: round(x,2),
    "propiedad": lambda x: "'" + str(x) + "'",
    "sucursal": lambda x: "'" + str(x) + "'",
    "poblacion": lambda x: "'" + str(x) + "'",
    "volumen": lambda x: round(x,2),
    "peso": lambda x: round(x,2)
}


MAX_CLIENTES = {
    "Propio": 5,
    "Tercero": 3
}