import machine
import time
from umqtt.simple import MQTTClient
import network
import dht
import ujson

# Configurações do AWS IoT Core
AWS_ENDPOINT = "a1qot9lnmmukni-ats.iot.us-east-1.amazonaws.com"  # substitua pelo seu endpoint AWS
CLIENT_ID = "Afill01"
TOPIC = "afill/data"

# Certificados e chaves
CERT_FILE = "cert/Afill.cert.pem"  # substitua com o caminho para seu certificado
KEY_FILE = "cert/Afill.private.key"  # substitua com o caminho para sua chave

try:
    with open(KEY_FILE, 'r') as f:
        key = f.read()
        print("Chave privada carregada com sucesso.")
except Exception as e:
    print("Erro ao ler a chave privada:", e)
    key = None

try:
    with open(CERT_FILE, 'r') as f:
        cert = f.read()
        print("Certificado carregado com sucesso.")
except Exception as e:
    print("Erro ao ler o certificado:", e)
    cert = None

ssl_params = {"key":key, "cert":cert, "server_side":False}

# Conecta ao Wi-Fi
def connect_wifi(ssid, senha):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Conectando ao Wi-Fi...")
        sta_if.active(True)
        sta_if.connect(ssid, senha)
        while not sta_if.isconnected():
            time.sleep(1)
    print("Conexão Wi-Fi estabelecida:", sta_if.ifconfig())

# Configura o MQTT com AWS IoT Core
def setup_mqtt():
    print("Configurando o MQTT...")
    print(f"AWS Endpoint: {AWS_ENDPOINT}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Certificado: {cert}")
    print(f"Chave: {key}")

    if cert is None or key is None:
        print("Certificado ou chave não carregados. Não é possível configurar o MQTT.")
        return None

    try:
        client = MQTTClient(
           client_id=CLIENT_ID, 
           server=AWS_ENDPOINT, 
           port=8883, 
           keepalive=1200, 
           ssl=True, ssl_params=ssl_params
        )
        client.connect()
        print("Conexão MQTT estabelecida.")
        return client
    except Exception as e:
        print("Erro ao conectar ao MQTT:", e)
        print("Detalhes da exceção:", str(e))


# Configuração do sensor DHT11 no pino GPIO 14
sensor = dht.DHT11(machine.Pin(14))

# Conectar ao Wi-Fi
connect_wifi("VISITANTE", "visitante01")

# Conectar ao MQTT
mqtt_client = setup_mqtt()
if mqtt_client is None:
    print("Falha na conexão MQTT. Encerrando o programa.")

# Loop principal para leitura do sensor e envio de dados
while True:
    try:
        time.sleep(2)
        sensor.measure()
        temp = sensor.temperature()  # temperatura em graus Celsius
        hum = sensor.humidity()      # umidade em %

        # Cria o payload JSON para enviar apenas temperatura e umidade
        # payload = '{{"temperatura": {:.1f}, "humidade": {:.1f}}}'.format(temp, hum)
        mesg = ujson.dumps({
            "temperatura": temp,
            "umidade": hum,
        })
        # Envia os dados para o AWS IoT Core
        mqtt_client.publish(TOPIC, mesg)
        print("Dados enviados:", mesg)

    except OSError as e:
        print("Falha ao ler o sensor:", e)
