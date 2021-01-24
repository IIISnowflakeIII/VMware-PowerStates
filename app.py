#!/usr/bin/env python3
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from pyVim import connect
from pyVmomi import vim
from os import environ
import logging
from time import time, sleep

# Get number of VM's powered on
def poweredOn(children):
  list = []
  for child in children:
    summary = child.summary
    state = (summary.runtime.powerState == "poweredOn" and summary.config.template == False)
    list.append(state)
  poweredOn = sum(list)
  print(str(poweredOn) + " virtual machines are powered on")
  return poweredOn
#endDef

# Get number of VM's powered off
def poweredOff(children):
  list = []
  for child in children:
    summary = child.summary
    state = (summary.runtime.powerState == "poweredOff" and summary.config.template == False)
    list.append(state)
  poweredOff = sum(list)
  print(str(poweredOff) + " virtual machines are powered off")
  return poweredOff
#endDef

# Write data to InfluxDB
def write_to_influx(client, database, children):
  measurement = {}
  measurement['measurement'] = 'vsphere_cluster_vmcount'
  measurement['tags'] = {}
  measurement['fields'] = {}
  measurement['fields']['poweredOn'] = poweredOn(children)
  measurement['fields']['poweredOff'] = poweredOff(children)
  try:
    client.switch_database(database)
    client.write_points([measurement])
    print("Exported to InfluxDB successfully")
    print("")
  except InfluxDBClientError as e:
    logging.error("Failed to export data to Influxdb: %s" % e)
#endDef

def main():
  print("Starting vSphere powrstate monitor...")
  
  # Get the variables set within Docker
  vcenter_host = environ['VCENTER_HOST']
  vcenter_usr = environ['VCENTER_USR']
  vcenter_pwd = environ['VCENTER_PWD']
  
  influx_host = environ['INFLUX_HOST']
  influx_usr = environ['INFLUX_USR']
  influx_pwd = environ['INFLUX_PWD']
  influx_db = environ['INFLUX_DB']
  
  # InfluxDB client 
  influx_client = InfluxDBClient(
    host=influx_host, 
    port=8086, 
    username=influx_usr, 
    password=influx_pwd
  )

  # vSphere client
  vsphere_client = connect.SmartConnectNoSSL (
    host=vcenter_host,
    user=vcenter_usr,
    pwd=vcenter_pwd
  )

  # Get virtual machines
  content = vsphere_client.RetrieveContent()
  container = content.rootFolder
  viewType = [vim.VirtualMachine]
  containerView = content.viewManager.CreateContainerView(
              container, viewType, recursive=True)
  children = containerView.view
  
  # Run every 60 seconds
  while True:
    sleep(60 - time() % 60)
    write_to_influx(influx_client, influx_db, children)

if __name__ == "__main__":
  main()