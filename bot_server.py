from flask import Flask
from flask import request
from fakenews101 import main
 
app = Flask(__name__)
 
@app.route("/", methods=["POST"])
def process_update():
	if request.method == 'POST':
		msg = request.get_json()
		main(msg)
		return "ok!", 200
