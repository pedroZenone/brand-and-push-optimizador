
from flask import Flask, request, jsonify
import time
import pandas as pd
from functions import *

app = Flask(__name__)
stat = 'idle'

@app.route('/post_data', methods=['POST'])
def post_data():
    global stat
    stat = 'bussy'
    try:
        data = request.json
        ids = ','.join([str(x) for x in data["ids"]])  # paso a string

        #### Fun start here
        log("", first=True)
        df = get_pedidos(ids) # filtro por los ids que me pasen
        meta_vehiculos_tarifario = get_trucks()
        incremental = get_incremental() # get las incremental id_run

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
        output["id_run"] = incremental-1 # Propio esta desfazado, piso con el id_run de Tercero

        log(f" Optimized data: {output.shape[0]}")

        if (output.shape[0] == 0):
            incremental = 0
        else:
            incremental -= 1 # avoid overlap in next interation

        save_run(incremental, df, meta_vehiculos_tarifario) # save logs and data to further reproduce output

        if(incremental > 0):
            insert_output(output,output_columns)  # save output in optimizer table
            # Inserto el input que no se optimizo
            un_optimized = df.loc[~df.id_item.isin(output.id_item.values)] # saco del input los que ya optimice
            un_optimized["id_run"] = incremental
            un_optimized["optimized"] = 0
            insert_output(un_optimized[base_columns],base_columns) # los datos que no me interesan los dejo nulos

        stat = 'idle'
        return (jsonify({"incremental": incremental}), 200)
    except Exception as e:
        log(f"ERROR:")
        log(str(e))
        stat = 'idle'
        save_run(incremental, df, meta_vehiculos_tarifario)  # save logs and data to further reproduce output
        return (jsonify({"error": str(e)}), 400)

@app.route('/status', methods=['GET'])
def status():
    global stat
    return (jsonify({"status": stat}), 200)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=APP_PORT)


# En digital ocean: https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3

# import requests
# response = requests.post('http://127.0.0.1:80/post_data', json={"key": "value"})
# print("Received response:", response.json())

# response = requests.get('http://127.0.0.1:80/status')
