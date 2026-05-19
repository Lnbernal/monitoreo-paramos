import paho.mqtt.client as mqtt
import json
from datetime import datetime
from db_config import insertar_lectura

MQTT_HOST = "6bf5f570aacb4000923acf3c45ae3734.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Florytech"
MQTT_PASS = "Florytech123*"
TOPIC_DATOS = "sensores/datos"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado a HiveMQ Cloud")
        client.subscribe(TOPIC_DATOS)
        print(f"Suscrito a: {TOPIC_DATOS}")
        print("Esperando datos del ESP32...")
    else:
        print(f"Error de conexion MQTT: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        temperatura = payload.get('temperatura')
        humedad_aire = payload.get('humedad_aire')
        humedad_suelo = payload.get('humedad_suelo')
        codigo_estacion = payload.get('estacion', 'PARAMO_001')
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Datos recibidos:")
        print(f"  Estacion: {codigo_estacion}")
        print(f"  Temperatura: {temperatura}C")
        print(f"  Humedad Aire: {humedad_aire}%")
        print(f"  Humedad Suelo: {humedad_suelo}%")
        
        insertar_lectura(codigo_estacion, temperatura, humedad_aire, humedad_suelo)
        
    except json.JSONDecodeError:
        print(f"Error decodificando JSON: {msg.payload}")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def start_listener():
    client = mqtt.Client()
    client.tls_set()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    
    print("Iniciando Listener MQTT...")
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_forever()

if __name__ == "__main__":
    start_listener()