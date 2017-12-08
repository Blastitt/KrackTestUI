from flask import Flask, request, session, render_template, render_template_string
import json
import os
from flask.ext.mysql import MySQL

mysql = MySQL()

app = Flask(__name__, static_url_path="", static_folder="static")

app.config['MYSQL_DATABASE_USER'] = 'kracktester'
app.config['MYSQL_DATABASE_PASSWORD'] = 'kracktester'
app.config['MYSQL_DATABASE_DB'] = 'KrackTestDb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

conn = mysql.connect();

cursor = conn.cursor();


@app.route('/devices')
def getDevices():

	cur = mysql.connect().cursor()

	cur.execute("SELECT * FROM devices")

	devices = cur.fetchall()

	print devices;

	return render_template('devicesFragment.html', devices=devices)

@app.route('/')
def index():

	return render_template('index.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
