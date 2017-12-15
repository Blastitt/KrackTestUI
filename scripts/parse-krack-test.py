from subprocess import Popen, PIPE, STDOUT
import MySQLdb
import sys

db = MySQLdb.connect(host='localhost',
	user='kracktester',
	passwd='kracktester',
	db='KrackTestDb')

cur = db.cursor()

command = './krackattacks-scripts-research/krackattack/krack-test-client.py'
if len(sys.argv) > 1:
	if sys.argv[1] == "--test":
		command = 'python parserTester.py'

	elif sys.argv[1] == "--clear":
		dropTableCmd = "DROP TABLE devices;"
		cur.execute(dropTableCmd)
		db.commit()
		db.close()
		exit(0)

createTableCmd = "CREATE TABLE IF NOT EXISTS devices \
(MacAddr VARCHAR(50) NOT NULL, \
	Status VARCHAR(50), \
	PRIMARY KEY (MacAddr));"

cur.execute(createTableCmd)
db.commit()


process = Popen(command, stdout=PIPE, shell=True)

clients = []
clientStatuses = []

def updateClient(client, status):
	if client not in clients:
		clients.append(client)
		clientStatuses.append(status)
		return True

	index = clients.index(client)

	if clientStatuses[index] != "Vulnerable":
		clientStatuses[index] = status
		return True

	return False # No update

while process.poll() is None:
	line = process.stdout.readline()

	words = line.split(' ')

	client = None
	clientStatus = None

	apStatus = "Offline"

	action = None


	if len(words) > 1 and words[1] == "Ready":
		apStatus = "Online"
		action = "Waiting for Connections"

	elif len(words) > 5 and words[5] == "associated":
		action = words[2] + " connected."
		client = words[2]
		clientStatus = "Testing"

	elif len(words) > 3 and words[3] == "DOESN'T":
		client = words[1][7:-1]
		clientStatus = "Patched"

		action = "STATUS CHANGED! " + client + ": " + clientStatus

	elif len(words) > 4 and words[4] == "all-zero":
		client = words[1][7:-1]
		clientStatus = "Vulnerable"

		action = "STATUS CHANGED! " + client + ": " + clientStatus

	elif len(words) > 4 and words[2] == "IV" and words[3] == "reuse" and words[4] == "detected":
		client = words [1][7:-1]
		clientStatus = "Vulnerable"

		action = "STATUS CHANGED! " + client + ": " + clientStatus

	elif len(words) > 13 and words[11] == "Client" and words[12] == "is" and words[13] == "vulnerable":
		client = words[1][7:-1]
		clientStatus = "Vulnerable"

		action = "STATUS CHANGED! " + client + ": " + clientStatus

	if client:
		if updateClient(client, clientStatus):
			sqlCmd = "INSERT INTO devices (MacAddr, Status) \
			VALUES ('{}', '{}') ON DUPLICATE KEY UPDATE \
			Status = '{}';".format(client, clientStatus, clientStatus)

			cur.execute(sqlCmd)
			db.commit()

	if action:
		print action
		
