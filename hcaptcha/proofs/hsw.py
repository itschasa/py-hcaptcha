from ..utils import is_main_process
import os
import random
import socketio
import subprocess
import threading
import time

if is_main_process():
    from flask import Flask
    from flask_socketio import SocketIO
    
    app = Flask(__name__)
    sio_server = SocketIO(app)

    @sio_server.on("request")
    def request_passer(data):
        sio_server.emit("request", data)

    @sio_server.on("response")
    def response_passer(token):
        sio_server.emit("response", token)

    @app.route("/")
    def index_view():
        with open("hcaptcha-js/hsw.js") as fp:
            code = fp.read()
        
        return """
        <html>
        <head></head>
        <body>
            <h1>OK</h1>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script>""" + code +"""</script>
            <script type="text/javascript" charset="utf-8">
                var socket = io()

                socket.on('connect', async function() {
                    setTimeout(() => location.reload(), 10000)
                })

                socket.on('connect_error', async function() {
                    location.reload()
                })

                socket.on('request', async function(data) {
                    let token = await hsw(data)
                    socket.emit('response', token)
                })
            </script>
        </body>
        </html>
        """
        
    threading.Thread(
        target=sio_server.run,
        daemon=True,
        args=(app,),
        kwargs={"port": 9932}
        ).start()

    if os.name == "nt":
        subprocess.call(["taskkill", "/f", "/im", "chrome.exe"])
        try:
            yesyeseysttstestbrowser = subprocess.Popen([
                os.environ["PROGRAMFILES(x86)"] + "/Google/Chrome/Application/chrome.exe",
                "--start-maximized",
                "--disable-gpu",
                "--new-window",
                "-incognito",
                "http://localhost:9932/"])
        except:
            yesyeseysttstestbrowser = subprocess.Popen([
                os.environ["PROGRAMFILES"] + "/Google/Chrome/Application/chrome.exe",
                "--start-maximized",
                "--disable-gpu",
                "--new-window",
                "-incognito",
                "http://localhost:9932/"])
    
    else:
        subprocess.call(["pkill", "-9", "chrome"])
        browser = subprocess.Popen([
            "google-chrome",
            "--start-maximized",
            "--disable-gpu",
            "--new-window",
            "-incognito",
            "http://localhost:9932/"])

sio = socketio.Client()
data_event = threading.Event()
proof_event = threading.Event()
proof_set_event = threading.Event()
latest_data = None
latest_proof = None

sio.connect("http://localhost:9932")

@sio.on("response")
def on_response(token):
    global latest_proof
    latest_proof = token
    proof_event.set()

def proof_updater():
    while True:
        try:
            data_event.wait()
            data_event.clear()
            sio.emit("request", latest_data)
            proof_event.wait(timeout=2)
            proof_event.clear()
            proof_set_event.set()
            time.sleep(0.2)
        except:
            pass
threading.Thread(target=proof_updater).start()

def get_proof(data):
    global latest_data
    latest_data = data
    data_event.set()
    proof_set_event.wait()
    proof = latest_proof
    proof += "".join(random.choices("ghijklmnopqrstuvwxyz", k=5))
    return proof
