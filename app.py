from flask import Flask, jsonify, render_template, request
import time
import os

app = Flask(__name__)

MAX_SAMPLES = 50

history = {
    "time": [],
    "adc1": [],
    "threshold": [],
    "pin23": [],
    "pwm": []
}

control = {
    "pwm": 50
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data", methods=["POST"])
def recibir_data():
    global history, control

    data = request.get_json()

    if not data:
        return jsonify({
            "ok": False,
            "error": "No JSON recibido"
        }), 400

    try:
        adc1 = float(data.get("adc1", 0))
        threshold = float(data.get("threshold", 2.5))
        pin23 = int(data.get("pin23", 0))
        pwm = int(data.get("pwm", control["pwm"]))

        history["time"].append(time.strftime("%H:%M:%S"))
        history["adc1"].append(adc1)
        history["threshold"].append(threshold)
        history["pin23"].append(pin23)
        history["pwm"].append(pwm)

        for key in history:
            if len(history[key]) > MAX_SAMPLES:
                history[key].pop(0)

        print("POST recibido:", data)

        return jsonify({
            "ok": True,
            "samples": len(history["adc1"]),
            "pwm": control["pwm"]
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400

@app.route("/history")
def history_route():
    return jsonify(history)

@app.route("/control_pwm", methods=["GET", "POST"])
def control_pwm():
    global control

    if request.method == "GET":
        return jsonify(control)

    data = request.get_json()

    if not data:
        return jsonify({
            "ok": False,
            "error": "No JSON recibido"
        }), 400

    try:
        pwm = int(float(data.get("pwm", control["pwm"])))
        pwm = max(0, min(100, pwm))

        control["pwm"] = pwm

        return jsonify({
            "ok": True,
            "pwm": control["pwm"]
        })

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400

@app.route("/debug")
def debug():
    return jsonify({
        "samples": len(history["adc1"]),
        "last_adc": history["adc1"][-1] if history["adc1"] else None,
        "history": history,
        "control": control
    })

@app.route("/status")
def status():
    return jsonify({
        "ok": True,
        "mode": "HTTP POST + PWM control",
        "samples": len(history["adc1"]),
        "control": control
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )