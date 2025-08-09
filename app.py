from flask import Flask
from controllers.bot_controller import bot_blueprint

app = Flask(__name__)
app.register_blueprint(bot_blueprint)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
