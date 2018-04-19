from libnmap.parser import NmapParser, NmapParserException
from libnmap.process import NmapProcess
import MySQLdb
from time import sleep
from netaddr import IPNetwork
import struct, fcntl, sys, socket

db = MySQLdb.connect(host='localhost',
    user='kracktester',
    passwd='kracktester',
    db='KrackTestDb')

cur = db.cursor()

if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        dropTableCmd = "DROP TABLE IF EXISTS scans, hosts, services;"
        cur.execute(dropTableCmd)
        db.commit()
        db.close()
        exit(0)

createScansTableCmd = "CREATE TABLE IF NOT EXISTS scans \
(StartTime VARCHAR(50) NOT NULL, \
    Status VARCHAR(50), \
    Progress FLOAT, \
    PRIMARY KEY (StartTime));"

cur.execute(createScansTableCmd)
db.commit()

createHostsTableCmd = "CREATE TABLE IF NOT EXISTS hosts \
(HostName VARCHAR(50), \
    IpAddr VARCHAR(50) NOT NULL, \
    ScanStartTime VARCHAR(50), \
    PRIMARY KEY (IpAddr, ScanStartTime));"

cur.execute(createHostsTableCmd)
db.commit()

createServicesTableCmd = "CREATE TABLE IF NOT EXISTS services \
(Id INT NOT NULL AUTO_INCREMENT, \
    Port INT, \
    IpAddr VARCHAR(50) NOT NULL, \
    ScanStartTime VARCHAR(50), \
    Protocol VARCHAR(10), \
    State VARCHAR(10), \
    Service VARCHAR(50), \
    Banner VARCHAR(100), \
    PRIMARY KEY (Id));"

cur.execute(createServicesTableCmd)
db.commit()

def getCIDR(ipAddr, netmask):
    return str(IPNetwork(ipAddr + '/' + netmask).cidr)

def getNetMask(interface):
    return socket.inet_ntoa(fcntl.ioctl(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), 
                             35099, struct.pack('256s', interface))[20:24])

def getIpAddr(interface):
    return socket.inet_ntoa(fcntl.ioctl(socket.socket(socket.AF_INET, socket.SOCK_DGRAM), 
                             0x8915, struct.pack('256s', interface[:15]))[20:24])

def do_scan(targets, options):
    parsed = None
    nmproc = NmapProcess(targets, options)
    nmproc.run_background()
    print("%d %d %d %d %d" % (nmproc.READY, nmproc.RUNNING, nmproc.FAILED, nmproc.CANCELLED, nmproc.DONE))

    

    while not nmproc.has_terminated():
        print("Nmap Scan running: ETC: {0} DONE: {1}%".format(nmproc.etc, nmproc.progress))
        insertScanCommand = "INSERT INTO scans (StartTime, Status, Progress) \
        VALUES ('{}', '{}', '{}') ON DUPLICATE KEY UPDATE \
        Progress = {};".format(nmproc.starttime, nmproc.state, nmproc.progress, nmproc.progress)
        cur.execute(insertScanCommand)
        db.commit()
        print('Updated scan in DB')
        sleep(2)

    insertScanCommand = "INSERT INTO scans (StartTime, Status, Progress) \
        VALUES ('{}', '{}', '{}') ON DUPLICATE KEY UPDATE \
        Progress = {};".format(nmproc.starttime, nmproc.state, nmproc.progress, nmproc.progress)
    cur.execute(insertScanCommand)
    db.commit()

    try:
        parsed = NmapParser.parse(nmproc.stdout)
    except NmapParserException as e:
        print("Exception raised while parsing scan: {0}".format(e.msg))

    return parsed

def parse_scan(nmap_report):
    #print("Starting Nmap {0} ( http://nmap.org ) at {1}".format(
    #    nmap_report.version,
    #    nmap_report.started))

    for host in nmap_report.hosts:
        if len(host.hostnames):
            tmp_host = host.hostnames.pop()
        else:
            tmp_host = ''

    #    print("Nmap scan report for {0} ({1})".format(
    #        tmp_host,
    #        host.address))
    #    print("Host is {0}.".format(host.status))
    #    print("  PORT     STATE         SERVICE")

        insertHostCommand = "INSERT INTO hosts (HostName, IpAddr, ScanStartTime) \
        VALUES ('{}', '{}', '{}');".format(tmp_host, host.address, nmap_report.started)
        cur.execute(insertHostCommand)
        db.commit()

        for serv in host.services:
            pserv = "{0:>5s}/{1:3s}  {2:12s}  {3}".format(
                    str(serv.port),
                    serv.protocol,
                    serv.state,
                    serv.service)
            if len(serv.banner):
                pserv += " ({0})".format(serv.banner)
    #        print(pserv)
            insertServiceCommand = "INSERT INTO services (Port, IpAddr, ScanStartTime, Protocol, State, Service, Banner) \
            VALUES ({}, '{}', '{}', '{}', '{}', '{}', '{}');".format(serv.port, host.address, nmap_report.started, serv.protocol, serv.state, serv.service, serv.banner)
            cur.execute(insertServiceCommand)
            db.commit()
    #print(nmap_report.summary)

def scanLocalNetwork(interface, arguments):
    subnet = getCIDR(getIpAddr(interface), getNetMask(interface))
    scan_and_report(subnet, arguments)

def scan_and_report(subnet, arguments):
    report = do_scan(subnet, arguments)
    if report:
        parse_scan(report)

def main():
    report = do_scan("127.0.0.1", "-sV")
    if report:
        parse_scan(report)
    else:
        print("No results returned")


if __name__ == '__main__':
    main()
    db.close()
