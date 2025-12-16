from dotenv import load_dotenv
import os

load_dotenv()

from app import createApp, socketio

app = createApp()

if __name__ == '__main__':
    app.debug = False

    socketio.run(
        app,
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
