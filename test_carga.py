import pandas as pd
from functions import *

if __name__ == '__main__':

    log("",first=True)
    df = get_pedidos()
    meta_vehiculos_tarifario = get_trucks()
    incremental = get_incremental()

    if((sum(df["peso"].isna()) + sum(df["volumen"].isna()) + sum(df["importe"].isna())) > 0):
        log(f'ALERTA! Dropeando registros {df.shape[0] - df[["peso","volumen","importe"]].dropna().shape[0]}')
        df = df.dropna(subset = ["peso","volumen","importe"])

    df["fecha"] = pd.to_datetime(df["fecha"],infer_datetime_format=True)
    df["dia"] = pd.to_datetime(df["fecha"].dt.date,infer_datetime_format=True)

    log(f" -------------------------------")
    log(f" Optimizando vehiculos Propios")
    log(f" -------------------------------")


    output_propio,pending,incremental = global_optimizer(df,meta_vehiculos_tarifario,"Propio",incremental)
    df_stage2 = df.loc[~df.id_item.isin(output_propio.id_item.values)]

    log(f" -------------------------------")
    log(f" Optimizando vehiculos Terceros")
    log(f" -------------------------------")

    output_tercero,pending,incremental = global_optimizer(df_stage2,meta_vehiculos_tarifario,"Tercero",incremental)
    output = pd.concat([output_propio,output_tercero],axis = 0)

    insert_output(output)

    print(output.shape)
    print(output.head())

    save_run(incremental,df,meta_vehiculos_tarifario)