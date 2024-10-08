import pandas as pd

APP_PORT = 5501
P_WEIGHT = 0.8
P_VOLUMEN = 0.8
OVER_WEIGHT = 1.2
OVER_VOLUME = 1.2
P_PRICE = 0.1
W_DELAY = 1  # Castigo para los que paquetes que van quedando viejos

truck_types = ['TRAILER','TORTON', 'CAMIONETA']

clasification_types = ['A','B','C']

base_columns = ["id_run","id_item", "cod_prod", "folio", "numdpc","sucursal","poblacion","poblacion_id",
                "volumen","peso","optimized", "descripcion","cant_autorizada","clasificacion"]

modeled_columns = ["placa", "id_vehiculo", "name_vehiculo", "price_warn", "grupo","precio_grupo",
                                 "precio_vehiculo", "propiedad","p_opt_weight","p_opt_vol","km_warn"]

output_columns = base_columns + modeled_columns

MAX_CLIENTES = {
    "Propio": 5,
    "Tercero": 3
}

str_lambda = lambda x: 'NULL' if x == None else "'" + str(x).replace("'",'"') + "'"

output_table_format = {
    "id_run": lambda x: int(x),
    "id_item": lambda x: int(x),
    "cod_prod": str_lambda,
    "folio": str_lambda,
    "numdpc": str_lambda,
    "grupo": str_lambda,
    "placa": str_lambda,
    "id_vehiculo": str_lambda,
    "name_vehiculo": str_lambda,
    "descripcion": str_lambda,
    "price_warn": lambda x: int(x),
    "precio_grupo": lambda x: round(x,2),
    "precio_vehiculo": lambda x: round(x,2),
    "p_opt_vol": lambda x: round(x,2),
    "p_opt_weight": lambda x: round(x,2),
    "propiedad": str_lambda,
    "sucursal": str_lambda,
    "poblacion": str_lambda,
    "poblacion_id": str_lambda,
    "volumen": lambda x: round(x,2),
    "peso": lambda x: round(x,2),
    "optimized": lambda x: int(x),
    "cant_autorizada": lambda x: round(x,2),
    "clasificacion":str_lambda,
    "km_warn": lambda x: int(x)
}

str_lambda_paralel = lambda x: None if x == None else str(x)
int_lambda = lambda x: None if pd.isna(x) else int(x)
float_lambda = lambda x: None if pd.isna(x) else round(x,2)

paralel_output_table_format = {
    "id_run": int_lambda,
    "id_item": int_lambda,
    "cod_prod": str_lambda_paralel,
    "folio": str_lambda_paralel,
    "numdpc": str_lambda_paralel,
    "grupo": str_lambda_paralel,
    "placa": str_lambda_paralel,
    "id_vehiculo": str_lambda_paralel,
    "name_vehiculo": str_lambda_paralel,
    "descripcion": str_lambda_paralel,
    "price_warn": int_lambda,
    "precio_grupo": float_lambda,
    "precio_vehiculo": float_lambda,
    "p_opt_vol": float_lambda,
    "p_opt_weight": float_lambda,
    "propiedad": str_lambda_paralel,
    "sucursal": str_lambda_paralel,
    "poblacion": str_lambda_paralel,
    "poblacion_id": str_lambda_paralel,
    "volumen": float_lambda,
    "peso": float_lambda,
    "optimized": int_lambda,
    "cant_autorizada": float_lambda,
    "clasificacion": str_lambda_paralel,
    "km_warn": int_lambda
}