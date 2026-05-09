from flask import Flask, jsonify, render_template
import paho.mqtt.client as mqtt
import json
import time
import threading
import os

app = Flask(__name__)

# ---------------- MQTT CONFIG ----------------
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "jcr/esp32_1/datos"

MAX_SAMPLES = 50

history = {
    "time": [],
    "adc1": [],
    "threshold": [],
    "pin23": []
}

# ---------------- MQTT CALLBACKS ----------------
def on_connect(client, userdata, flags, rc):
    print("MQTT conectado. Código:", rc)
    client.subscribe(TOPIC)
    print("Suscrito a:", TOPIC)

def on_message(client, userdata, msg):
    global history

    try:
        payload = msg.payload.decode()
        data = json.loads(payload)

        print("MQTT recibido:", data)

        adc1 = float(data.get("adc1", 0))
        threshold = float(data.get("threshold", 2.5))
        pin23 = int(data.get("pin23", 0))

        history["time"].append(time.strftime("%H:%M:%S"))
        history["adc1"].append(adc1)
        history["threshold"].append(threshold)
        history["pin23"].append(pin23)

        for key in history:
            if len(history[key]) > MAX_SAMPLES:
                history[key].pop(0)

    except Exception as e:
        print("Error procesando MQTT:", e)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Mantiene MQTT vivo en este hilo.
    # Paho recomienda loop_start() o loop_forever()
    # para mantener activa la red MQTT.
    client.loop_forever()

mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# ---------------- FLASK ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history")
def get_history():
    return jsonify(history)

@app.route("/status")
def status():
    return jsonify({
        "ok": True,
        "topic": TOPIC,
        "samples": len(history["adc1"])
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)