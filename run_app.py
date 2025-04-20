import webbrowser
from threading import Timer
from app import app  # your Flask instance

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(port=5000, threaded=True)