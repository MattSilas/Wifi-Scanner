# OSX and Windows Wifi Scanner
# Created by Matt Silas
import sys
import plistlib
import json
import urllib
import logging
import subprocess
import re

def find_access_points_osx():
    """
    Parses the output from the airport utility into a single dictionary
    Airport's output is a plist; a list of dictionaries
    Keys can repeat for each plist node, so the values are appended into a list, to avoid overwriting
    Updated for OS X 10.10
    :return: dictionary with output from airport scan
    """
    from commands import getoutput
    scan = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s -x'   
    root = getoutput(scan)
    output = plistlib.readPlistFromString(root)
    info = {}
    for node in output:
        temp_dict = parse_plist_output(node)
        for k, v in temp_dict.iteritems():
            if k in info:
                if isinstance(info[k], list):
                    info[k] = info[k] + [v]
                else:
                    info[k] = [info[k], v]
            else:
                info[k] = v
    return info

def parse_plist_output(node):
    """
    Parses a plist node, which can contain nested dictionaries
    The nested items are pulled out into a single k, v pair.
    If the same key is present in the dictionary, create a list of values
    :param node: dictionary
    :return: dictionary
    """
    return_val = {}
    try:
        for key, value in node.iteritems():
            if isinstance(value, dict):
                return_val.update(parse_plist_output(value))
            else:
                if key in return_val:
                    if isinstance(return_val[key], list):
                        return_val[key] = return_val[key] + [value]
                    else:
                        return_val[key] = [return_val[key], value]
                else:
                    return_val[key] = value
    except Exception as e:
        logging.exception("key: %s, value: %s", (key, value))

    return return_val

#Runs win32 netsh utility and searches for BSSID and RSSI based on regex    
def find_access_points_win():   
    scan = 'cmd.exe /c netsh wlan show network mode=Bssid | findstr "BSSID Signal"'
    root = subprocess.check_output(scan)
    ap_list = root.decode()
    mac_address = '([a-fA-F0-9]{1,2}[:]?){6}'
    c = re.compile(mac_address).finditer(ap_list)
    access_points = {}
    signals = get_sig_strength_win(ap_list)
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


def parameters(signals):
    """
    Gets the RSSI and BSSID from the signals
    :param signals: dictionary from wifi scan
    :return: url encoded data request
    """
    data = {'BSSID': [], 'RSSI': []}
    keys = ['BSSID', 'RSSI']
    for key in keys:
        data[key].append(signals[key])

    return urllib.urlencode(data, True).replace("%3A", ":")

if __name__ == "__main__":
    print "Finding Access Points"
    if sys.platform == 'darwin':
        access_points = find_access_points_osx()
    if sys.platform == 'linux2'or sys.platform == 'linux':
        print "no linux support currently"
        exit
    if sys.platform == 'win32':
        access_points = find_access_points_win()
        
    print "Econding Parameters"
    params = parameters(access_points)
    url = "INSERT HERE"

    f = urllib.urlopen(url %params)
    print "Retrieving JSON"
    print f.read()
