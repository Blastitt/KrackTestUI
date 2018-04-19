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

@app.route('/devices')
def getDevices():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices")

    devices = cur.fetchall()
    conn.close()

    return render_template('devicesFragment.html', devices=devices)

@app.route('/scanFragment')
def getLatestScan():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scans ORDER BY StartTime DESC LIMIT 1")
    scan = cur.fetchone()
    latestScan = {
    'start_time': float(scan[0]),
    'status': int(scan[1]),
    'progress': int(scan[2])
    }
    conn.close()
    return render_template('scanFragment.html', scan=latestScan)

@app.route('/start-scan', methods=['POST'])
def startScan():
    scanThread = threading.Thread(target=network_scanner.scanLocalNetwork, args=("eth0", "-sV"), kwargs={})
    scanThread.start()
    return('', 204)

@app.route('/services', methods=['GET'])
def showServices():
    return render_template('services.html')

@app.route('/servicesFragment', methods=['GET'])
def getServiceReport():
    scanId = request.args.get('scanId')
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM scans WHERE Progress=100 ORDER BY StartTime DESC LIMIT 1")
    scan = cur.fetchone()

    cur.execute("SELECT * FROM hosts WHERE ScanStartTime={0}".format(float(scan[0])))
    hostResults = cur.fetchall()

    cur.execute("SELECT * FROM services WHERE ScanStartTime={0}".format(float(scan[0])))
    serviceResults = cur.fetchall()

    conn.close()


    serviceResults = sorted(serviceResults, key=lambda entry: entry[2])
    hostResults = sorted(hostResults, key=lambda entry: entry[1])

    services = []
    detectedHosts = []
    hosts = []

    for entry in serviceResults:
        service = {
        'port': float(entry[1]),
        'host': entry[2],
        'name': entry[6],
        'banner': entry[7] or "No Info",
        }
        services.append(service)
        detectedHosts.append(service['host'])

    for entry in hostResults:
        host = {
        'hostname': entry[0],
        'ipaddr': entry[1]
        }
        if host['ipaddr'] in detectedHosts:
        	hosts.append(host)

    return render_template('servicesFragment.html', services=services, hosts=hosts)

@app.route('/krack')
def krack():

    return render_template('krack.html')



@app.template_filter('ctime')
def timectime(s):
    return ctime(s) # datetime.datetime.fromtimestamp(s)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
