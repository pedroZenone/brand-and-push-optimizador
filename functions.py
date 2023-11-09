import pandas as pd
from ortools.linear_solver import pywraplp
import numpy as np
from datetime import datetime
import random
import string
import pymssql
from defines import *
import psycopg2
import os
import shutil
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "secrets.env"))  # load passwords

def optimize(data, bag):
    solver = pywraplp.Solver.CreateSolver('SCIP')
    #solver.SetSolverSpecificParametersAsString('presolving/maxrounds', '0')
    
    data.update(bag)  # se lo apendeo al diccionario

    # Prepare solver matrix
    x = {}
    for i in data['items']:
        for j in data['bags']:
            x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

    # Constraint for an item being placed in 1 knapsack
    for i in data['items']:
        solver.Add(sum(x[i, j] for j in data['bags']) <= 1)

    # Knapsack max Constraint
    for j in data['bags']:
        solver.Add(sum(x[(i, j)] * data['weights'][i] for i in data['items']) <= data['bag_weight'][j]*OVER_WEIGHT)
        solver.Add(sum(x[(i, j)] * data['volume'][i] for i in data['items']) <= data['bag_volume'][j]*OVER_VOLUME)
        # solver.Add(sum(x[(i,j)]*data['price'][i] for i in data['items'])*P_PRICE >= data['bag_price'][j])

    # Create binary variables to represent the conditions
    use_condition1 = {}
    use_condition2 = {}

    for j in data['bags']:
        use_condition1[j] = solver.IntVar(0, 1, f'use_condition1_{j}')
        use_condition2[j] = solver.IntVar(0, 1, f'use_condition2_{j}')

    # Add constraints for conditions

    for j in data['bags']:
        limit_v = data['bag_volume'][j] * P_VOLUMEN
        solver.Add(
            sum(x[(i, j)] * data['volume'][i] for i in data['items']) >= limit_v - limit_v * (1 - use_condition1[j]))
        limit_w = data['bag_weight'][j] * P_WEIGHT
        solver.Add(
            sum(x[(i, j)] * data['weights'][i] for i in data['items']) >= limit_w - limit_w * (1 - use_condition2[j]))

    # Add a constraint that ensures at least one condition is satisfied for each bag
    for j in data['bags']:
        solver.Add(use_condition1[j] + use_condition2[j] >= 1)

    # Maximize value, I can manage delay
    objective = solver.Objective()
    for i in data['items']:
        for j in data['bags']:
            objective.SetCoefficient(x[(i, j)], data['values'][i])
    objective.SetMaximization()

    solv = solver.Solve()

    # Restore information
    l_ = [[]]

    if solv == pywraplp.Solver.OPTIMAL:
        for j in data['bags']:
            for i in data['items']:
                if x[i, j].solution_value() > 0:
                    l_[j] += [i]
    return l_[0]  # This is one bag problem


def generate_item_data(raw_data,clients_order):
    data = {}
    
    # Aplico un ponderador en base a la distancia para que si hay dos paquetes iguales de fierentes sucursales, eliga la mas lejana
    sucursales = [x["numdpc"] for x in raw_data]
    ponderador = {j:1+(x/100) for x,j in zip(
        [i for i,x in reversed(list(enumerate(clients_order)))],clients_order)} # Hago un rank y luego armo un dict de mapeo sucursal - rank   
    data['values'] = [ponderador[x] for x in sucursales]
    #data['values'] = [1 + (datetime.today() - pd.to_datetime(x["fecha"])).days * W_DELAY for x in raw_data]
    
    data['weights'] = [x["peso"] for x in raw_data]
    data['volume'] = [x["volumen"] for x in raw_data]
    data['price'] = [x["importe"] for x in raw_data]

    data['items'] = list(range(len(raw_data)))
    data['num_items'] = len(raw_data)
    
    return data


def get_available_truck(metadata, poblacion, volumen, weight, truck, propiedad):
    # Saco duplicados por si tengo repetidos los coches
    metadata = metadata.drop_duplicates(subset=["tipo_vehiculo", "poblacion"])
    # Me traigo todas las poblaciones que venimos relevando en la ruta de reparto
    metadata = metadata[metadata["poblacion"].isin(poblacion)]

    if (metadata.shape[0] == 0):
        if (propiedad == "Tercero"):
            log(f"Polacion intermedia inicial, se saltea hasta encontrar poblacion destino en ruta reparto")
        else:
            log(f"Se agotaron las placas para estos destinos")
        return None

    puntos_intermedios = len(
        poblacion) - metadata.poblacion.nunique()  # si hay intermedias quiero acomodar las poblaciones reales en ruta
    # agrupo con el precio maximo
    metadata = metadata.groupby(["tipo_vehiculo", "id_vehiculo"], as_index=False).agg(
        {"capacidad_volumen": "max", "capacidad_peso": "max",
         "tarifa": "max", "poblacion": "size", "placas": "max"})
    # solo me quedo con los vehiculos que estan disponibles en todos los puntos de la ruta
    metadata = metadata.loc[metadata.poblacion == (len(poblacion) - puntos_intermedios)]

    posibles_camiones = metadata[((metadata.capacidad_peso * P_WEIGHT <= weight) |
                                 (metadata.capacidad_volumen * P_VOLUMEN <= volumen)
                                 ) & (metadata.tipo_vehiculo == truck)]
    
    # Si no encuentro soluciones
    if (posibles_camiones.shape[0] == 0):
        return None

    #camion = posibles_camiones.sort_values(by="capacidad_peso", ascending=False).to_dict("records")[n]  # me traigo el camion pero indexado por iteracion n
    camion = posibles_camiones.to_dict("records")[0]
    # price = tarifas[(tarifas.POBLACION == poblacion) & (tarifas.TIPO_VEHICULO == camion["TIPO_VEHICULO"])].to_dict("records")[0]

    bag = {}
    bag['bag_weight'] = [camion["capacidad_peso"]]
    bag['bag_volume'] = [camion["capacidad_volumen"]]
    bag['bag_price'] = [camion["tarifa"]]
    bag["name"] = camion["tipo_vehiculo"]
    bag["id"] = camion["id_vehiculo"]
    bag["placa"] = camion["placas"]
    # I wanted to change the values at a later data
    bag['bags'] = list(range(1))

    return bag


def log(x, first=False, printer=False, file_name="log.txt"):
    file_path = os.path.dirname(__file__)
    x = str(x)

    if (first):
        with open(os.path.join(file_path,file_name), 'w') as f:
            f.write(x + "\n")
    else:
        with open(os.path.join(file_path,file_name), 'a') as f:
            f.write(x + "\n")

    if (printer):
        print(x)


def rand_name(n):
    return ''.join(random.choices(string.digits, k=n))


def get_truck_id(metadata, bag, propiedad):
    """
    Para propiedad Tercero genera una placa aleatoria
    Para propiedad Propios quito el vehiculo de los disponibles propios para no volver a usarlo y retorno placa
    """
    if (propiedad == "Propio"):
        placa = bag["placa"]
        metadata = metadata.loc[metadata.placas != bag["placa"]]
    else:  # Terceros
        placa = bag["placa"] + rand_name(5)
    return metadata, placa


def get_pedidos(ids = None):
    server = os.getenv("mssql_server")
    database = os.getenv("mssql_database")
    username = os.getenv("mssql_username")
    password = os.getenv("mssql_password")

    if(ids):
        query_where = f"WHERE id in ({ids})"
    else:
        query_where = ""

    # Create a connection
    connection = pymssql.connect(server=server, user=username, password=password, database=database)
    # Create a cursor
    cursor = connection.cursor()
    # Execute a query
    cursor.execute(f"""
        SELECT p.ID as ID_ITEM, COD_PROD,DESCRIPCION,FOLIO,CANTIDAD_AUTORIZADA, IMPORTE, PESO, VOLUMEN, NUMDPC, SUCURSAL,
            nombre as POBLACION, poblacion as ID_POBLACION, distancia, RUTA_REPARTO, RUTA_REPARTO as ID_RUTA_REPARTO, CURRENT_TIMESTAMP
        FROM dbo.pedidos_optimizacion p
        {query_where}
    """)

    r = cursor.fetchall()
    pedidos = pd.DataFrame(r,
                           columns=["id_item", "cod_prod", "descripcion", "folio", "cant_autorizada", "importe", "peso",
                                    "volumen", "numdpc", "sucursal", "poblacion", "poblacion_id", "distancia",
                                    "ruta_reparto", "id_ruta_reparto", "fecha"])

    pedidos["sucursal"] = pedidos["sucursal"].str.strip()
    pedidos["poblacion"] = pedidos["poblacion"].str.strip()
    pedidos["ruta_reparto"] = pedidos["ruta_reparto"].str.strip()
    pedidos["peso"] = pd.to_numeric(pedidos["peso"], errors='coerce')
    pedidos["importe"] = pd.to_numeric(pedidos["importe"], errors='coerce')
    pedidos["volumen"] = pd.to_numeric(pedidos["volumen"], errors='coerce')

    connection.close()

    return pedidos


def get_trucks():
    server = os.getenv("mssql_server")
    database = os.getenv("mssql_database")
    username = os.getenv("mssql_username")
    password = os.getenv("mssql_password")

    # Create a connection
    connection = pymssql.connect(server=server, user=username, password=password, database=database)

    # Create a cursor
    cursor = connection.cursor()

    # Execute a query
    cursor.execute("""
        SELECT PLACAS,PROPIEDAD,ID as ID_VEHICULO,v.TIPO_VEHICULO,ID_POBLACION,v.POBLACION, TARIFA , DISTANCIA, 
            capacidadPeso, capacidadVolumen
        FROM dbo.vehiculos_disponibles v
    """)

    r = cursor.fetchall()
    vehiculos = pd.DataFrame(r, columns=["placas", "propiedad", "id_vehiculo", "tipo_vehiculo", "id_poblacion",
                                         "poblacion","tarifa", "distancia", "capacidad_peso", "capacidad_volumen"])

    vehiculos["tipo_vehiculo"] = vehiculos["tipo_vehiculo"].str.strip()
    vehiculos["poblacion"] = vehiculos["poblacion"].str.strip()
    vehiculos["capacidad_peso"] = pd.to_numeric(vehiculos["capacidad_peso"], errors='coerce')
    vehiculos["capacidad_volumen"] = pd.to_numeric(vehiculos["capacidad_volumen"], errors='coerce')
    vehiculos["tarifa"] = pd.to_numeric(vehiculos["tarifa"], errors='coerce')

    connection.close()
    return vehiculos


def global_optimizer(df, meta_vehiculos_tarifario, propiedad, incremental):
    FECHA = datetime.today().strftime('%d-%m-%Y')  # Solo dejo esto para usarlo para pesar por delay

    # Mappers para logear mas elegante
    id2sucursal = {x[1]: x[2] for x in df[["numdpc", "sucursal"]].drop_duplicates(subset=["numdpc"]).itertuples()}
    id2dist = {x[1]: x[2] for x in
               df[["numdpc", "distancia"]].groupby("numdpc", as_index=False).max().itertuples()}  # just in case

    max_clientes = MAX_CLIENTES[propiedad]
    metadata_vehiculos = meta_vehiculos_tarifario.loc[meta_vehiculos_tarifario.propiedad == propiedad]
    
    ready = []
    pending_day = []

    if (propiedad == "Propio"):
        df = df.loc[df.poblacion.isin(
            metadata_vehiculos.poblacion.values)]  # Solo se trabajan con las localidades con disponibilidad

    for r in df.ruta_reparto.unique():
        log(f"\n ***** Optimize ruta n°: {r} ******** \n")
        
        df_ruta = df.loc[(df.ruta_reparto == r)]

        # Armo un mapeo de cliente a poblacion
        client2pob = {}
        tmp = df_ruta.sort_values(by=["distancia", "poblacion"], ascending=False)[
            ["numdpc", "poblacion"]].drop_duplicates(subset="numdpc")
        for t in tmp.itertuples():
            client2pob.update({t[1]: t[2]})

        for truck_type in truck_types:
            log(f"++++++++ Iteracion {truck_type} ++++++++")
            
            clients = df_ruta.sort_values(by=["distancia","poblacion"], ascending=False)["numdpc"].drop_duplicates().to_list()
            
            # Voy a forzar tener una ventana de max_clientes al inicio
            n = min(len(clients),max_clientes) - 1 # le resto 1 para despues agregarselo en el while
            client_ruta = clients[0:n]
            clients = clients[n:] # vacio clients. nunca puede estar vacia por el n-1
            #client_ruta = []
            
            while (len(clients) > 0):
                client_ruta += [clients.pop(0)]
                # Para cada reparto, como maximo puede haber MAX_CLIENTES
                if (len(client_ruta) > max_clientes):
                    client_ruta.pop(0)
    
                pob_ruta = list(set([client2pob[x] for x in client_ruta]))  # poblaciones de los cliente seleccionados
                log(f"++ Clients to optimize: {[id2sucursal[x] for x in client_ruta]} |  Poblaciones: {pob_ruta} ++")
    
                pending = [] # Voy a usar esto para no optimizar lo mismo en el for 50
                
                # Los items a ser procesados son los de los clientes que no fueron optimizados en otra iteracion
                to_process = df_ruta.loc[(df_ruta.numdpc.isin(client_ruta)) & 
                                         (~df_ruta.id_item.isin([x["id_item"] for x in ready]))]
                pending = to_process.to_dict('records')
    
                ready_iter = []  # guardo en esta variable para identificar cuando resuelve un camion dentro del loop
                for i in range(50):  # itero 50 veces por poner un numero grande
                    # parseo la data para tenerla en el formato encesario para el opti
                    data_to_optimize = generate_item_data(pending,client_ruta)  
    
                    total_volume = sum(data_to_optimize["volume"])
                    total_weight = sum(data_to_optimize["weights"])
                    total_price = sum(data_to_optimize["price"])
                    
                    if (i == 0):
                        log(f"Trying to optimize products: {len(data_to_optimize['volume'])}, volume: {round(total_volume, 2)}, weight:{round(total_weight, 2)}, price: {round(total_price, 2)}")
    
                    # me fijo que camion tengo disponible
                    bag = get_available_truck(metadata_vehiculos, pob_ruta, total_volume,
                                              total_weight, truck_type, propiedad)
    
                    if (bag == None):  # si con el peso y volumen no se cumplen las condiciones minimas, termino de loopear
                        log("No possible bag")
                        break  # Ya no hay mas camiones para probar
    
                    items_bag = optimize(data_to_optimize, bag)  # optimizo en base al camion disponible
                    log(f"Trying with bag: {bag['name']} and optimized: {len(items_bag)}")
    
                    if (len(items_bag) == 0):
                        break # Si no encuentra solucion sigo acumulando sucursales
    
                    # Updateo los items listos y los pendientes
                    ready_iter = list(np.array(pending)[items_bag])
    
                    ready_price = sum([x["importe"] for x in ready_iter])
                    ready_weight = sum([x["peso"] for x in ready_iter])
                    ready_volume = sum([x["volumen"] for x in ready_iter])
                    price_rule = 1 if ready_price * P_PRICE < bag['bag_price'][
                        0] else 0  # si el 10% del valor del pedido es inferior a la tarifa de translado alerto
                    volumen_percentage_load = ready_volume / bag['bag_volume'][0]
                    weight_percentage_load = ready_weight / bag['bag_weight'][0]
    
                    if((volumen_percentage_load < P_VOLUMEN) & (weight_percentage_load < P_WEIGHT) ): # Falsa alarma del optimizador?
                        break
    
                    metadata_vehiculos, bag_id = get_truck_id(metadata_vehiculos, bag,
                                                              propiedad)  # asigno un nombre al camion y saco la placa propia de la lista para no volver a usarla
    
                    for i in range(len(ready_iter)):  # Le agrego la metadata del envio
                        ready_iter[i].update({"placa": bag_id, "id_vehiculo": bag["id"], "name_vehiculo": bag["name"],
                                              "precio_vehiculo": bag['bag_price'][0],
                                              "precio_grupo": total_price, "price_warn": price_rule,
                                              "grupo": f"GB{incremental}",
                                              "p_opt_vol": 100 * volumen_percentage_load,
                                              "p_opt_weight": 100 * weight_percentage_load,
                                              "propiedad": propiedad,"optimized":1})
    
                    log(f"ID track: {bag_id}")
    
                    incremental += 1
                    # pending: los que me quedaron rezagados, del total que no estna en ready
                    pending = list(np.array(pending)[[x for x in range(len(pending)) if x not in items_bag]])
    
                    if (len(ready_iter) > 0):
                        log(f"pendings: {len(pending)}")
    
                    ready += ready_iter  # save interation

            #if (len(ready_iter) > 0):  # Si encuentro solucion limpio las rutas posibles y empiezo a acumular con el siguiente destino
            #    client_ruta = []
            #    log("> Clean clients and start to acumulate again")

    if (len(ready) > 0):
        output = pd.DataFrame(ready)
        output["id_run"] = int(incremental)
        output = output[output_columns]
    else:
        output = pd.DataFrame([], columns=output_columns)

    pending_day = df.loc[~df_ruta.id_item.isin([x["id_item"] for x in ready])] # excluyo lo optimizado
    return output, pd.DataFrame(pending_day, columns=df.columns), incremental

def insert_output(output,cols):
    # PostgreSQL connection parameters
    db_params = {
        'host': os.getenv("post_host"),
        'port': os.getenv("post_port"),
        'database': os.getenv("post_database"),
        'user': os.getenv("post_user"),
        'password': os.getenv("post_password")
    }

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()

    # itero por todas las rows y voy insertando de a una
    col_name = ','.join(cols)
    for ind, line in output.iterrows():
        col_values = ','.join([str(output_table_format[x](line[x])) for x in cols])
        cursor.execute(f"INSERT INTO optimizer ({col_name}) VALUES ({col_values})")

    conn.commit() # mando a insertar
    cursor.close()
    conn.close()

def paralel_insert_output(output,cols):
    if(output.shape[0] == 0):
        return None

    # Postregs conn
    db_params = {
        'host': os.getenv("post_host"),
        'port': os.getenv("post_port"),
        'database': os.getenv("post_database"),
        'user': os.getenv("post_user"),
        'password': os.getenv("post_password")
    }

    # Adapt column format
    for c in cols:
        output[c] = output[c].apply(lambda x: paralel_output_table_format[c](x))

    # Create a SQLAlchemy engine
    engine = create_engine(
        f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}',poolclass=NullPool)
    connection = engine.connect()
    # Insert DataFrame in batches

    chunksize = 1000  # Adjust as needed
    output.to_sql('optimizer', connection, if_exists='append', index=False, chunksize=chunksize)
    connection.close()
    engine.dispose()

def get_incremental():
    db_params = {
        'host': os.getenv("post_host"),
        'port': os.getenv("post_port"),
        'database': os.getenv("post_database"),
        'user': os.getenv("post_user"),
        'password': os.getenv("post_password")
    }

    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    # Siempre inserto en la tabla como GBxxx donde xxx es el numero incremental
    cursor.execute("SELECT MAX(CAST(SUBSTRING(grupo FROM 3) AS INTEGER)) as incremental, count(1) from optimizer")
    incremental = cursor.fetchall()
    conn.close()

    if(len(incremental) > 0):
        if(incremental[0][1] == 0):
            return 1 # optimizer table is empty, empiezo de 1 porque siempre resto 1 al optimizar
        else:
            return int(incremental[0][0]) + 1 # siempre le agrego 1 al ultimo valor
    else:
        raise(Exception("Bad format in grupo column of optimizer table"))

def save_run(incremental,input,trucks):
    file_path = os.path.dirname(__file__)

    try: # save  run cannot fail
        if(not os.path.exists(f"logs/{incremental}")):
            os.makedirs(os.path.join(file_path,f"logs/{incremental}"))
        shutil.copy2(os.path.join(file_path,'log.txt'), os.path.join(file_path,f"logs/{incremental}/log.txt"))

        if (not os.path.exists(os.path.join(file_path,f"input_data/{incremental}"))):
            os.makedirs(os.path.join(file_path,f"input_data/{incremental}"))
        input.to_csv(os.path.join(file_path,f"input_data/{incremental}/input.csv"),index=False)

        if (not os.path.exists(os.path.join(file_path,f"trucks_data/{incremental}"))):
            os.makedirs(os.path.join(file_path,f"trucks_data/{incremental}"))
        trucks.to_csv(os.path.join(file_path,f"trucks_data/{incremental}/trucks.csv"),index=False)
    except:
        pass


