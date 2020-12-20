#!/usr/bin/env python3
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from pyVim import connect
from pyVmomi import vim
from os import environ, write
import logging
import schedule
import time

#Get host variables
vcenter_host = environ['VCENTER_HOST']
vcenter_usr = environ['VCENTER_USR']
vcenter_pwd = environ['VCENTER_PWD']
influx_host = environ['INFLUX_HOST']
influx_usr = environ['INFLUX_USR']
influx_pwd = environ['INFLUX_PWD']
influx_db = environ['INFLUX_DB']

#Influx client 
influx_client = InfluxDBClient(
  host=influx_host, 
  port=8086, 
  username=influx_usr, 
  password=influx_pwd
)

#VSphere client
vsphere_client = connect.SmartConnectNoSSL (
  host=vcenter_host,
  user=vcenter_usr,
  pwd=vcenter_pwd
)

content = vsphere_client.RetrieveContent()

container = content.rootFolder
viewType = [vim.VirtualMachine]
containerView = content.viewManager.CreateContainerView(
            container, viewType, recursive=True)

children = containerView.view

#Get number of VM's powered on
def poweredOn():
  list = []
  for child in children:
    summary = child.summary
    state = (summary.runtime.powerState == "poweredOn" and summary.config.template == False)
    list.append(state)
  x = sum(list)
  return x

#Get number of VM's powered off
def poweredOff():
  list = []
  for child in children:
    summary = child.summary
    state = (summary.runtime.powerState == "poweredOff" and summary.config.template == False)
    list.append(state)
  x = sum(list)
  return x

#Print powerStates
print(str(poweredOn()) + " powered on")
print(str(poweredOff()) + " powered off")

#Writes data to InfluxDB
def write_to_influx():
        measurement = {}
        measurement['measurement'] = 'vsphere_cluster_vmcount'
        measurement['tags'] = {}
        measurement['fields'] = {}
        measurement['fields']['poweredOn'] = poweredOn()
        measurement['fields']['poweredOff'] = poweredOff()
        try:
          influx_client.switch_database(influx_db)
          influx_client.write_points([measurement])
          print("Exported to InfluxDB successfully")
        except InfluxDBClientError as e:
          logging.error("Failed to export data to Influxdb: %s" % e)

if __name__ == "__main__":
  schedule.every(1).minutes.do(write_to_influx)
  while 1:
    schedule.run_pending()
    time.sleep(1)