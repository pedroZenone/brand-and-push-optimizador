import pandas as pd
from functions import *
import time

#ids = "'3039901','3039908','3024785','3024786','3035897','3035896','3007688','3007674','3007670','3007683'"

if __name__ == '__main__':

    log("", first=True)
    start_time = time.time()
    df = get_pedidos()  # filtro por los ids que me pasen
    print("--- %s seconds Pedidos---" % (time.time() - start_time))
    start_time = time.time()
    meta_vehiculos_tarifario = get_trucks()
    print("--- %s seconds Trucks---" % (time.time() - start_time))
    start_time = time.time()
    incremental = get_incremental()  # get las incremental id_run
    print("--- %s seconds get incremental---" % (time.time() - start_time))

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

    log(f" Optimized data: {output.shape[0]}",time=True)

    if (output.shape[0] == 0):
        incremental = 0
    else:
        incremental -= 1  # avoid overlap in next interation

    save_run(incremental, df, meta_vehiculos_tarifario)  # save logs and data to further reproduce output

    if (incremental > 0):
        #paralel_insert_output(output, output_columns)  # save output in optimizer table
        start_time = time.time()
        bulk_insert(output, output_columns)
        print("--- %s seconds first bulk---" % (time.time() - start_time))

        # Inserto el input que no se optimizo
        un_optimized = df.loc[~df.id_item.isin(output.id_item.values)]  # saco del input los que ya optimice
        un_optimized["id_run"] = incremental
        un_optimized["optimized"] = 0
        #paralel_insert_output(un_optimized[base_columns], base_columns)  # los datos que no me interesan los dejo nulos
        start_time = time.time()
        bulk_insert(un_optimized[base_columns], base_columns)
        print("--- %s seconds second bulk---" % (time.time() - start_time))

    output.to_csv("test2.csv",index=False)
    un_optimized.to_csv("test_unpotimized2.csv", index=False)

