from flask import Flask,render_template
from models import *
from routes.workout_gen import workout_gen

app = Flask(__name__)
app.register_blueprint(workout_gen,url_prefix='/workout')


app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fitted.db"

db.init_app(app)

with app.app_context():
   db.create_all()

@app.route("/")
def index():
    return render_template('workout_creator.html')

if __name__ == "__main__":
    app.run(debug=True)