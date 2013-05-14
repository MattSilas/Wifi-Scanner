#OSX Wifi Scanner

from commands import getoutput
import json
import xml.etree.ElementTree
import urllib, webbrowser

#Runs OSX Airport utility with scan and xml out flags set
def find_access_points():
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

#Converts the Airport XML to JSON
def xml_to_json(signals):
    data = {"ap": []}

    for address, rssi in signals.items():
        ap = {"mac_address": address, "values": rssi}
        data["ap"].append(ap)

    return json.JSONEncoder().encode(data)

#Encodes the the access point data as parameters to send data
#to the URL as a GET request. Data2 was created to support the
#way the API is currently written. Once a decision is made either
#data2 or data will be destroyed
def parameters(signals):
    data = {'MAC':[], 'RSSI':[]}
    for address, rssi in signals.items():
        data["MAC"].append(address)
        data["RSSI"].append(rssi)
    return urllib.urlencode(data,True).replace("%3A",":")

if __name__ == "__main__":
    print "Finding Access Points"
    access_points = find_access_points()
    print "URL encoding the parameters"
    params = parameters(access_points)
    url = "http://web.engr.oregonstate.edu/~silasm/CS419/API.php?%s"
    print params
    f = urllib.urlopen(url %params)
    print f.read()
    webbrowser.open_new_tab(url % params)
    
     
