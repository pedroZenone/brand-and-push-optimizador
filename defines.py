APP_PORT = 5501
P_WEIGHT = 0.8
P_VOLUMEN = 0.8
P_PRICE = 0.1
W_DELAY = 1  # Castigo para los que paquetes que van quedando viejos

base_columns = ["id_run","id_item", "cod_prod", "folio", "numdpc","sucursal","poblacion","volumen","peso","optimized",
                "descripcion"]
output_columns = base_columns + ["placa", "id_vehiculo", "name_vehiculo", "price_warn", "grupo","precio_grupo",
                                 "precio_vehiculo", "propiedad","p_opt_weight","p_opt_vol"]
output_table_format = {
    "id_run": lambda x: int(x),
    "id_item": lambda x: int(x),
    "cod_prod": lambda x: "'" + str(x).replace("'",'"') + "'",
    "folio": lambda x: "'" + str(x).replace("'",'"') + "'",
    "numdpc": lambda x: "'" + str(x).replace("'",'"') + "'",
    "grupo": lambda x: "'" + str(x).replace("'",'"') + "'",
    "placa": lambda x: "'" + str(x).replace("'",'"') + "'",
    "id_vehiculo": lambda x: "'" + str(x).replace("'",'"') + "'",
    "name_vehiculo": lambda x: "'" + str(x).replace("'",'"') + "'",
    "descripcion": lambda x: "'" + str(x).replace("'",'"') + "'",
    "price_warn": lambda x: int(x),
    "precio_grupo": lambda x: round(x,2),
    "precio_vehiculo": lambda x: round(x,2),
    "p_opt_vol": lambda x: round(x,2),
    "p_opt_weight": lambda x: round(x,2),
    "propiedad": lambda x: "'" + str(x).replace("'",'"') + "'",
    "sucursal": lambda x: "'" + str(x).replace("'",'"') + "'",
    "poblacion": lambda x: "'" + str(x).replace("'",'"') + "'",
    "volumen": lambda x: round(x,2),
    "peso": lambda x: round(x,2),
    "optimized": lambda x: int(x)
}

paralel_output_table_format = {
    "id_run": lambda x: int(x),
    "id_item": lambda x: int(x),
    "cod_prod": lambda x: str(x),
    "folio": lambda x:  str(x),
    "numdpc": lambda x:  str(x),
    "grupo": lambda x:  str(x),
    "placa": lambda x:  str(x),
    "id_vehiculo": lambda x:  str(x),
    "name_vehiculo": lambda x:  str(x),
    "descripcion": lambda x:  str(x),
    "price_warn": lambda x: int(x),
    "precio_grupo": lambda x: round(x,2),
    "precio_vehiculo": lambda x: round(x,2),
    "p_opt_vol": lambda x: round(x,2),
    "p_opt_weight": lambda x: round(x,2),
    "propiedad": lambda x: str(x),
    "sucursal": lambda x: str(x),
    "poblacion": lambda x: str(x),
    "volumen": lambda x: round(x,2),
    "peso": lambda x: round(x,2),
    "optimized": lambda x: int(x)
}


MAX_CLIENTES = {
    "Propio": 5,
    "Tercero": 3
}