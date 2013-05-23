#OSX and Windows Wifi Scanner
#Created by Matt Silas

import json, sys
import xml.etree.ElementTree
import urllib, webbrowser

#Runs OSX Airport utility with scan and xml out flags set
def find_access_points_osx():
    from commands import getoutput
    scan = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s -x'   
    root = xml.etree.ElementTree.fromstring(getoutput(scan))
    output = root.getchildren()[0]

    access_points = {}

    for access_point in output:
        # 1st string is MAC address
        address = access_point.find("string").text
        # 2nd string is SSID
        #ssid = access_point.findall("string")[1].text
        # 8th integer is signal strength
        strength = abs(int(access_point.findall("integer")[7].text))
        access_points[address] = strength

    return access_points

#Runs win32 netsh utility and searches for BSSID and RSSI based on regex    
def find_access_points_win():   
    scan = 'cmd.exe /c netsh wlan show network mode=Bssid | findstr "BSSID Signal"'
    root=subprocess.check_output(scan)
    ap_list = root.decode()
    mac_address = '([a-fA-F0-9]{1,2}[:]?){6}'
    c = re.compile(mac_address).finditer(ap_list)
    access_points={}
    signals =get_sig_strength_win(ap_list)
    x=0
    if c:
        for y in c:
            access_points[(ap_list[y.start(): y.end()])]=signals[x]
            x=x+1
    return access_points
  
#returns array of all RSSIs from scan 
def get_sig_strength_win(ap_list):
    sig_strength = r'([\d\d]+)%'
    c = re.findall(sig_strength,ap_list)
    if c:
        return c
    
#Converts the Airport XML to JSON, currently not utilized
def xml_to_json(signals):
    data = {"ap": []}
    for address, rssi in signals.items():
        ap = {"mac_address": address, "values": rssi}
        data["ap"].append(ap)
    return json.JSONEncoder().encode(data)

#Encodes the the access point data as parameters to send data
#to the URL as a GET request.
def parameters(signals):
    data = {'MAC':[], 'RSSI':[]}
    for address, rssi in signals.items():
        data["MAC"].append(address)
        data["RSSI"].append(rssi)
    return urllib.urlencode(data,True).replace("%3A",":")

if __name__ == "__main__":
    print "Finding Access Points"
    if sys.platform == 'darwin':
        access_points = find_access_points_osx()
    if sys.platform == 'linux2'or sys.platform == 'linux':
        print "no linux support currently"
        exit
    if sys.platform == 'win32':
        access_points = find_access_points_win32()
        
    print "Econding Parameters"
    params = parameters(access_points)
    url = "INSERT HERE"

    f = urllib.urlopen(url %params)
    print "Retrieving JSON"
    print f.read()
    #webbrowser.open_new_tab(url % params)
    
     
