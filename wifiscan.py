#OSX Wifi Scanner

from commands import getoutput
import json
import xml.etree.ElementTree

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
        ssid = access_point.findall("string")[1].text
        # 8th integer is signal strength
        strength = abs(int(access_point.findall("integer")[7].text))
        access_points[address] = strength, ssid

    return access_points

#Converts the Airport XML to JSON
def xml_to_json(signals):
    data = {"access_points": []}

    for address, attributes in signals.items():
        ap = {"mac_address": address, "values": attributes}
        data["access_points"].append(ap)

    return json.JSONEncoder().encode(data)


if __name__ == "__main__":
    print "Finding Access Points"
    access_points = find_access_points()
    json = xml_to_json(access_points)
