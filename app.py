from app import create_app
import json

with open('config.json') as config_file:
    config = json.load(config_file)

app = create_app()

app.config['SECRET_KEY'] = 'your_secret_key_here'


if __name__ == "__main__":
    # enable handling multiple concurrent requests in the dev server
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
