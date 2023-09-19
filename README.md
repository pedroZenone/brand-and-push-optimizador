## Descripcion de funcionamiento

1- Desde el backend llega un POST por REST con un json que contiene un array de IDs a ser consultados en el ERP del cliente

2- Se extrae info de pedidos a optimizar y vehiculos disponibles

3- El modelo genera un ID de corrida que obtiene de la ultimo corriga, mirando el cambio grupo que esta formado por GBxxx donde se toma el max(xxx) + 1

4- Se aplica algoritmo de optimizacion, cargando los retultados en la tabla optimizer del postgres productivo. Con la columna id_run referenciamos el ID de la corrida

5- Se guarda en logs/id_run/ un txt con todo el proceso que uso el modelo para optimizar. En al carpta input_data/id_run y tracus_data/id_run se guardan los datos que se trajeron para que pueda haber repetibilidad del proceso


## Pasos para correr por primera vez en la instancia.

1- Cargar los secrets:
scp secrets.env root@IP_SERVIDOR:/root/secrets.env

2- Entrar a la instancia: ssh root@IP_SERVIDOR

3- Clonar el repo: git clone https://github.com/pedroZenone/brand-and-push-optimizador.git
4- Correr el script: 
sudo /bin/bash ~/brand-and-push-optimizador/starter_scripts/iniate_server.sh

5- Ya esta corriendo el scripts!

## Utilidades:

* Para ver logs:
journalctl -u systemd_app.service > app_logs.txt

* Para ver si systemd lo tiene activo el proceso: 
systemctl status systemd_app.service

* Para correr una prueba con full carga: python3 test_carga.py

* Para probar que esta funcionando:

Para ver consultar status del proceso:
```
import requests
response = requests.get('http://IP_SERVIDOR:5501/status')
response.json()
```

Para correr el modelo:
```
import requests
response = requests.post('http://206.189.207.216:5501/post_data', json={"ids": [2766093,2766064]})
print("Received response:", response.json())
```
