import pandas as pd
from functions import *

#ids = "'2866135','2866137','2866123','2866125','2865769','2858909','2864077','2798639','2798640','2798637','2798638','2866131','2866133'"

if __name__ == '__main__':

    log("", first=True)

    df = get_pedidos()  # filtro por los ids que me pasen
    meta_vehiculos_tarifario = get_trucks()
    incremental = get_incremental()  # get las incremental id_run

    if ((sum(df["peso"].isna()) + sum(df["volumen"].isna()) + sum(df["importe"].isna())) > 0):
        log(f'ALERTA! Dropeando registros {df.shape[0] - df[["peso", "volumen", "importe"]].dropna().shape[0]}')
        df = df.dropna(subset=["peso", "volumen", "importe"])

    df["fecha"] = pd.to_datetime(df["fecha"], infer_datetime_format=True)
    df["dia"] = pd.to_datetime(df["fecha"].dt.date, infer_datetime_format=True)

    log(f" -------------------------------")
    log(f" Optimizando vehiculos Propios")
    log(f" -------------------------------")

    output_propio, pending, incremental = global_optimizer(df, meta_vehiculos_tarifario, "Propio", incremental)
    df_stage2 = df.loc[~df.id_item.isin(output_propio.id_item.values)]

    log(f" -------------------------------")
    log(f" Optimizando vehiculos Terceros")
    log(f" -------------------------------")

    output_tercero, pending, incremental = global_optimizer(df_stage2, meta_vehiculos_tarifario, "Tercero",
                                                            incremental)
    output = pd.concat([output_propio, output_tercero], axis=0)
    output["id_run"] = incremental - 1  # Propio esta desfazado, piso con el id_run de Tercero

    log(f" Optimized data: {output.shape[0]}")

    if (output.shape[0] == 0):
        incremental = 0
    else:
        incremental -= 1  # avoid overlap in next interation

    save_run(incremental, df, meta_vehiculos_tarifario)  # save logs and data to further reproduce output

    if (incremental > 0):
        #insert_output(output, output_columns)  # save output in optimizer table
        # Inserto el input que no se optimizo
        un_optimized = df.loc[~df.id_item.isin(output.id_item.values)]  # saco del input los que ya optimice
        un_optimized["id_run"] = incremental
        un_optimized["optimized"] = 0
        #insert_output(un_optimized[base_columns], base_columns)  # los datos que no me interesan los dejo nulos
        print(incremental)

    output.to_csv("test2.csv",index=False)
    un_optimized.to_csv("test_unpotimized2.csv", index=False)

