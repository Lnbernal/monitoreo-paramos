import paho.mqtt.client as mqtt
import json
from datetime import datetime
from db_config import insertar_lectura

MQTT_HOST  = "6bf5f570aacb4000923acf3c45ae3734.s1.eu.hivemq.cloud"
MQTT_PORT  = 8883
MQTT_USER  = "Florytech"
MQTT_PASS  = "Florytech123*"
TOPIC_DATOS = "sensores/datos"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado a HiveMQ Cloud")
        client.subscribe(TOPIC_DATOS)
        print(f"[MQTT] Suscrito a: {TOPIC_DATOS}")
    else:
        print(f"[MQTT] Error de conexión: rc={rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Desconectado (rc={rc}). Reconectando automáticamente...")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        temperatura     = payload.get('temperatura')
        humedad_aire    = payload.get('humedad_aire')
        humedad_suelo   = payload.get('humedad_suelo')
        codigo_estacion = payload.get('estacion', 'SUMA_001')

        print(f"[MQTT] [{datetime.now().strftime('%H:%M:%S')}] "
              f"{codigo_estacion} | T:{temperatura}°C "
              f"HA:{humedad_aire}% HS:{humedad_suelo}%")

        insertar_lectura(codigo_estacion, temperatura, humedad_aire, humedad_suelo)

    except json.JSONDecodeError:
        print(f"[MQTT] JSON inválido: {msg.payload}")
    except Exception as e:
        print(f"[MQTT] Error procesando mensaje: {e}")

def start_listener():
    """
    Inicia el cliente MQTT con reconexión automática.
    Función bloqueante — debe llamarse desde un thread.
    """
    client = mqtt.Client()
    client.tls_set()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # Reconexión automática cada 5 segundos si falla
    client.reconnect_delay_set(min_delay=5, max_delay=30)

    print(f"[MQTT] Conectando a {MQTT_HOST}:{MQTT_PORT}...")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()   # bloquea el thread, reconecta solo

# Solo si se ejecuta directamente (pruebas locales)
if __name__ == "__main__":
    start_listener()