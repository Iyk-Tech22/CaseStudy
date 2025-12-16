from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # IMPORTANT: avoid Werkzeug dev reloader on Windows with Flask-SocketIO
    app.debug = False  # make sure Flask itself is not in debug mode

    socketio.run(
        app,
        host='127.0.0.1',   # local only
        port=5000,
        debug=False,        # do NOT enable debug here
        use_reloader=False, # critical to avoid WinError 10038
        allow_unsafe_werkzeug=True,
    )