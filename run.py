import sys
sys.path.append('./scripts')
from flask import Flask, request, session, render_template, render_template_string
import json
import os
from flask.ext.mysql import MySQL
from libnmap.process import NmapProcess
from time import sleep, ctime
import threading
import network_scanner


mysql = MySQL()

app = Flask(__name__, static_url_path="", static_folder="static")

app.config['MYSQL_DATABASE_USER'] = 'kracktester'
app.config['MYSQL_DATABASE_PASSWORD'] = 'kracktester'
app.config['MYSQL_DATABASE_DB'] = 'KrackTestDb'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql.init_app(app)

conn = mysql.connect();

cur = conn.cursor();

@app.route('/devices')
def getDevices():

    cur.execute("SELECT * FROM devices")

    devices = cur.fetchall()

    print devices;

    return render_template('devicesFragment.html', devices=devices)

@app.route('/scanFragment')
def getLatestScan():
	cur.execute("SELECT * FROM scans ORDER BY StartTime DESC LIMIT 1")
	scan = cur.fetchone()
	print scan
	latestScan = {
		'start_time': float(scan[0]),
		'status': int(scan[1]),
		'progress': int(scan[2])
	}
	return render_template('scanFragment.html', scan=latestScan)

@app.route('/start-scan', methods=['POST'])
def startScan():
	scanThread = threading.Thread(target=network_scanner.scan_and_report, args=("127.0.0.1", "-sV"), kwargs={})
	scanThread.start()

@app.route('/services', methods=['GET'])
def showServices():
	return render_template('services.html')

@app.route('/servicesFragment', methods=['GET'])
def getServiceReport():
	return render_template('servicesFragment.html')

@app.route('/krack')
def krack():

    return render_template('krack.html')



@app.template_filter('ctime')
def timectime(s):
    return ctime(s) # datetime.datetime.fromtimestamp(s)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
