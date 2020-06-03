#!/usr/bin/python
# -*- coding=gbk -*-
# -*- conding: UTF-8 -*-

from requests import get,post
from os import name,getenv,system
from time import sleep
from psutil import pids,Process
from configparser import ConfigParser
import pycurl
import sys
import certifi
import traceback
from urllib.parse import urlparse
import subprocess 
import re



try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
# prometheus client
import prometheus_client
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client.core import CollectorRegistry
import psutil


def hostname():
    sys=name
    if sys == 'nt':
      hostname=getenv('computername')
      return hostname
    elif sys == 'posix':
      hostname = host.read()
      return hostname
    else:
      return 'Unknow Hostname'

config = ConfigParser()
config.read('getinfo.cfg')
# get localhost ip
mylocalhost=config['local']["ip"]
print(mylocalhost)
mylocalport=config['local']["port"]
print(mylocalport)
# example localurl=http://127.0.0.1:9182/metrics
localurl='http://' + mylocalhost + ':' + mylocalport + '/metrics'

# get job name and instance name
pmh=config['jobname']["suffix"]
job_name= hostname() + company
instance_name= hostname()
print( 'instance name: ', instance_name )

# get pushgateway host
pushhost = config['pushgateway']['host']
pushport = config['pushgateway']['port']
pushhostinfo = pushhost + ':' +pushport
pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name
#print(pushurl)

#get username and password
username = config['auth']['username']
password = config['auth']['password']

# curl
class Test:
    def __init__(self):
      self.contents = ''
    def body_callback(self,buf):
      self.contents = self.contents + buf.decode()
#获取WEB 响应性能指标
def m_web():
  kvs = config.options("site")
  for value_url in kvs:
   try:
    # Print wwwsinacom
    inputurl=config.get("site",value_url)
    print ('curl url: ',inputurl)

    inputdomain=urlparse(inputurl).netloc
    print ('get domain: ',inputdomain)

    monitorurl = 'monitorurl'
    t = Test()
    #gzip_test = file("gzip_test.txt", 'w')
    
    c = pycurl.Curl()
    c.setopt(pycurl.WRITEFUNCTION,t.body_callback)
    c.setopt(pycurl.ENCODING, 'gzip')
    #是否屏蔽下载进度条，非0则屏蔽
    c.setopt(pycurl.NOPROGRESS, 1)
    c.setopt(pycurl.FORBID_REUSE, 1)
    c.setopt(pycurl.NOBODY, True)
    c.setopt(pycurl.CAINFO, certifi.where())
    c.setopt(pycurl.USERAGENT,"Mozilla/64.2 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET ; CLR 2.0.50324)")
    c.setopt(pycurl.URL,inputurl)
    c.perform()
   except:
    traceback.print_exc()
    print ('curl error... ...')
    sleep(0.5)
    continue ;
   else:
    http_code = c.getinfo(pycurl.HTTP_CODE)
    dns_resole = c.getinfo(pycurl.NAMELOOKUP_TIME)
    #从建立连接到传输开始消耗的时间
    http_starttransfer_time = c.getinfo(pycurl.STARTTRANSFER_TIME)
    ##从发起请求到SSL建立握手时间
    ssl_time = c.getinfo(pycurl.APPCONNECT_TIME)  
    #建立连接所消耗的时间
    http_conn_time = c.getinfo(pycurl.CONNECT_TIME)
    #从建立连接到准备传输所消耗的时间
    http_pretransfer_time = c.getinfo(pycurl.PRETRANSFER_TIME)
    http_total_time = c.getinfo(pycurl.TOTAL_TIME)
    c.close()

    print ("http_starttransfer_time %f" %(http_starttransfer_time*1000))
    print ("dns_resole %f" %(dns_resole *1000))
    print ("http_code %d" %http_code)
    print ("http_conn_time %f" %(http_conn_time*1000))
    print ("http_pretransfer_time %f" %(http_pretransfer_time*1000))
    print ("http_total_time %f" %(http_total_time*1000))
    print('ssl_time: %f' %(ssl_time*1000))
    
    REGISTRY = CollectorRegistry(auto_describe=False)

    client_curl = Gauge("http_code",name,["inputdomain"],registry=REGISTRY)
    client_curl.labels(inputurl).set(http_code)

    client_curl = Gauge("dns_resole",name,["monitorurl"],registry=REGISTRY)
    client_curl.labels(inputurl).set(dns_resole * 1000)

    client_curl = Gauge("http_starttransfer_time",name,["monitorurl"],registry=REGISTRY)
    client_curl.labels(inputurl).set(http_starttransfer_time * 1000)

    client_curl = Gauge("http_conn_time",name,["monitorurl"],registry=REGISTRY)
    client_curl.labels(inputurl).set(http_conn_time * 1000)

    client_curl = Gauge("http_pretransfer_time",name,["monitorurl"],registry=REGISTRY)
    client_curl.labels(inputurl).set(http_pretransfer_time *1000)

    client_curl = Gauge("http_total_time",name,["monitorurl"],registry=REGISTRY)
    client_curl.labels(inputurl).set(http_total_time * 1000)

    pushurl_web = pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name + '_' + inputdomain
    post(pushurl_web,data=prometheus_client.generate_latest(REGISTRY),timeout=60,auth=(username,password))
    print('push to url: ',  pushurl_web)
    print('pushurl_web finished!')
    print()
#获取WEB 响应性能指标
def m_ping():
      kvsping = config.options("ping")
      t = Test()
      for value_ping in kvsping:
        ping_addr=config.get("ping",value_ping)
        # ping start process.
        res=subprocess.Popen('ping ' + ping_addr + ' -n 5' + ' -w 2000',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        resStr=(str(res.stdout.read(),encoding='gbk'))
        #pLose.findall(r)[-3]
        print('source info: ',resStr)

        try:

          reLose = re.compile('\(\d{1,6}% 丢失\)')
          pLoseNum=str(reLose.findall(resStr)).split('%')[0].replace('[\'(','')
          print('Lose Packet: ',pLoseNum)

        except:
          traceback.print_exc()
          pAvgNum='-20'
          print('Lose Packet: ',pLoseNum)
	  
        try:
          reAvg = re.compile('平均 = \d{1,6}ms')
          if reAvg.findall(resStr):
            pAvgNum=str(reAvg.findall(resStr)).split('= ')[-1].replace('ms\']','')
            print('Avg Packet: ',pAvgNum)
          else:
            pAvgNum='-30'
            print('Avg Packet: ',pAvgNum)
        except:
         traceback.print_exc()
         pAvgNum='-10'
         print('Avg Packet: ',pAvgNum)

        try:
          reIpv4 = re.compile('(?:[0-9]{1,3}\.){3}[0-9]{1,3}')
          ipv4 = str(reIpv4.findall(resStr)[0])
          print('Ipv4: ',ipv4)

        except:
          traceback.print_exc()
          ipv4='0.0.0.0'
          print('except ipv4: ',ipv4)
        
        try:
          reIpv6 = re.compile('(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}',re.I)
          if reIpv6.findall(resStr):
            ipv6 = str(reIpv6.findall(resStr)[0])
          else:
            ipv6 = str('::')
            print('ipv6 is: ',ipv6)
        except:
          traceback.print_exc()
          ipv6='::'
          print('ipv6: ',ipv6)
        REGISTRY = CollectorRegistry(auto_describe=False)
        client_curl = Gauge("ping_loss",name,["ping","ipv4","ipv6"],registry=REGISTRY)
        client_curl.labels(ping_addr,ipv4,ipv6).set(pLoseNum)

        client_curl = Gauge("ping_avg",name,["ping","ipv4","ipv6"],registry=REGISTRY)
        client_curl.labels(ping_addr,ipv4,ipv6).set(pAvgNum)
        pushurl_addr = pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name + '_ping' + value_ping
        post(pushurl_addr,data=prometheus_client.generate_latest(REGISTRY),timeout=60,auth=(username,password))
        print('push to ping : ',  pushurl_addr)
        print('pushurl_addr finished!')
        print()

def getIp():
        try:
          print('_____________  start  get ip  ____________')
          sleep(3)
          req = get("http://txt.go.sohu.com/ip/soip")
          ip = re.findall(r'\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}',req.text)
          wanIp = ip[0]
          publicIp = 'publicIp'
          print ("pubilc IP: ",ip[0])
          REGISTRY = CollectorRegistry(auto_describe=False)
          client_curl = Gauge("wanIp",name,["wanIp"],registry=REGISTRY)
          client_curl.labels(wanIp).set(0)
          print('_____________________________________________')
          pushurl_addr = pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name
          post(pushurl_addr,data=prometheus_client.generate_latest(REGISTRY),timeout=60,auth=(username,password))

          print('wanIp url : ',  pushurl_addr)
          print('______________  end get ip _______________')
        except:
          traceback.print_exc()
          wanIp = '0.0.0.0'
          print('wanIP: ',wanIp)
          REGISTRY = CollectorRegistry(auto_describe=False)
          client_curl = Gauge("wanIp",name,["wanIp"],registry=REGISTRY)
          client_curl.labels(wanIp).set(0)
          pushurl_addr = pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name
          post(pushurl_addr,data=prometheus_client.generate_latest(REGISTRY),timeout=60,auth=(username,password))

          print ('__________ getIp except_____________________')
def getNetInfo():
        try:
          p = subprocess.Popen(["ipconfig", "/all"], stdout=subprocess.PIPE).communicate()[0].decode("gbk")
          pp = p.replace(' ','')
          print('process ipconfig all output : ',pp)
          ipInfo = pp
          print('ipInfo: ',ipInfo)
          REGISTRY = CollectorRegistry(auto_describe=False)
          client_curl = Gauge("localNetInfo",name,["localNetInfo"],registry=REGISTRY)
          client_curl.labels(ipInfo).set(0)
          pushurl_addr = pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name
          post(pushurl_addr,data=prometheus_client.generate_latest(REGISTRY),timeout=60,auth=(username,password))
        except:
          ipInfo = 'get error ... ... !!! !!!'
          traceback.print_exc()
          print (netInfo)
          REGISTRY = CollectorRegistry(auto_describe=False)
          client_curl = Gauge("localNetInfo",name,["localNetInfo"],registry=REGISTRY)
          client_curl.labels(ipInfo).set(0)
          pushurl_addr = pushurl='http://' + pushhostinfo + '/metrics/job/' + job_name + '/instance/' + instance_name
          post(pushurl_addr,data=prometheus_client.generate_latest(REGISTRY),timeout=60,auth=(username,password))

def run():
      try:
        #local 127.0.0.1:9182/metrics
        r=get(localurl)
        print(r.status_code)
        content=r.text.replace('# TYPE process_start_time_seconds counter','# TYPE process_start_time_seconds gauge')
        post(pushurl,data=content,timeout=60,auth=(username,password))

        print('push to url:',pushurl)
        print('push finished!')
        print()
        sleep(1)
      except:
        sleep(1)
        print('post Error ... ... sleep 3s ... ... run post pushurl ')


if __name__ == '__main__':
  sleep(300)
  while True:
    try:
      getIp()
      getNetInfo()
      run()
      m_web()
      m_ping()

      sleep(600)
    except:
      traceback.print_exc()
      print('may any error.. .. ..')
      sleep(300)
