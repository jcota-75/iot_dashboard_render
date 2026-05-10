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

    global mqtt_status

    mqtt_status["connected"] = (rc == 0)
    mqtt_status["rc"] = rc
    mqtt_status["error"] = None

    print("MQTT conectado. Código:", rc)

    client.subscribe(TOPIC)

    print("Suscrito a:", TOPIC)

def on_message(client, userdata, msg):

    global history
    global mqtt_status

    try:

        payload = msg.payload.decode()

        mqtt_status["last_message"] = payload

        data = json.loads(payload)

        adc1 = float(data.get("adc1", 0))
        threshold = float(data.get("threshold", 2.5))
        pin23 = int(data.get("pin23", 0))

        history["time"].append(time.strftime("%H:%M:%S"))
        history["adc1"].append(adc1)
        history["threshold"].append(threshold)
        history["pin23"].append(pin23)

    except Exception as e:

        mqtt_status["error"] = str(e)

        print("Error MQTT:", e)
@app.route("/mqtt_status")
def mqtt_debug():
    return jsonify(mqtt_status)

def start_mqtt():
    global mqtt_status

    mqtt_status["error"] = "start_mqtt iniciado"

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        mqtt_status["error"] = "intentando conectar al broker"

        client.connect(BROKER, PORT, 60)

        mqtt_status["error"] = "connect() ejecutado, entrando a loop_forever"

        client.loop_forever()

    except Exception as e:
        mqtt_status["connected"] = False
        mqtt_status["error"] = str(e)
        print("ERROR MQTT:", e)

mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# ---------------- FLASK ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/history")
def get_history():
    return jsonify(history)

mqtt_status = {
    "connected": False,
    "rc": None,
    "last_message": None,
    "error": None
}
@app.route("/debug")
def debug():
    return jsonify({
        "samples": len(history["adc1"]),
        "last_adc": history["adc1"][-1] if history["adc1"] else None,
        "history": history
    })


mqtt_status = {
    "connected": False,
    "rc": None,
    "last_message": None,
    "error": None
}
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
