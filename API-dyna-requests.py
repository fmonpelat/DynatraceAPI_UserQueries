#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 15:43:30 2020

@author: Facundo Monpelat

MIT License

Copyright (c) [2020] [PowerCloud]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import json
import requests
import urllib.parse
from datetime import datetime
from datetime import timedelta
import os
import pandas as pd
import argparse
import textwrap
import sys


def main():
 
    parser = argparse.ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=textwrap.dedent(''' \
                                            -- Dynatrace USQL report exporter
                                            --------------------------------------------------------------------------
                                            Example of use:
                                                Normal execution (without start or end time),start time is:
                                                    first exec: 
                                                        now() - 24 Hs
                                                    with file time (lastTimestamp.json):
                                                        readed end time
                                                end time is always exec time.
                                                    $ '''+__file__+'''
                                                with only start time (end time is exec time):
                                                    $ '''+__file__+''' -s "2020-06-29 00:00+0000"'
                                                with only end time (start time is exec time - 24 Hs):
                                                    $ '''+__file__+''' -e "2020-06-30 08:00+0000" -v'
                                                with start time and end time set:
                                                    $ '''+__file__+''' -s "2020-06-29 00:00+0000" -e "2020-06-30 08:00+0000"'
                                            ---------------------------------------------------------------------------
                                            '''))
    parser.add_argument("-v","--verbose", action='store_true',help="Increase output verbosity")
    parser.add_argument("-o","--output", default="data/data",help="Output path + filename, Default: data/data_<timestamp>.csv")
    parser.add_argument("-x","--outputmode",default="csv",help="Output file: json or csv, Default: csv")
    parser.add_argument("-s","--starttime", help="Start time date in format: %%Y-%%m-%%d %%H:%%M%%z")
    parser.add_argument("-e","--endtime", help="End time date in format: %%Y-%%m-%%d %%H:%%M%%z")
    args = parser.parse_args()
    
    verbose = 0

    if args.output:
        ouputFilename = args.output
        
    if args.outputmode:
        filemode = args.outputmode
        
    if args.verbose:
        verbose = 1
        print("Verbosity turned on")
    
    if args.starttime:
        # override set starttime
        t_start = datetime.strptime(args.starttime,
                                             '%Y-%m-%d %H:%M%z')
        
    if args.endtime:
        # override set endtime
        t_end = datetime.strptime(args.endtime, 
                                           '%Y-%m-%d %H:%M%z')
        
    if not args.starttime:
        # calculate startime = now()-24 hs
        t_start = datetime.now() - timedelta(days=1)        
    if not args.endtime:
        # calculate endtime = now()
        t_end = datetime.now()


    if (not args.starttime) and (not args.endtime):
        # Normal mode: Automatic processing time with file
        # Time file not found starttime = now()-24hs, endtime = now()
        # Time file found starttime = file_time, endtime = now()
        filename = 'lastTimestamp.json'
        if os.path.isfile('./' + filename) == True:
            # The file was found ...
            with open(filename, 'r', encoding='utf-8') as f:
                time = json.load(f)
                t_start = datetime.fromtimestamp(time['timestamp_end'])
                t_end = datetime.now()
        
    # format time in epoch in milliseconds
    dt_from = int((t_start.timestamp()*1000))
    dt_to = int((t_end.timestamp()*1000))
    # Time dictionary
    time = dict({'timestamp_start': dt_from/1000,
                 'timestamp_end': dt_to/1000,
                 'timestamp_format': "seconds",
                 'timestamp_timezone': 'local'})

    if verbose == 1:
        print('From timestamp (ms): ' + str(dt_from))
        print('To timestamp (ms): ' + str(dt_to))
    
    
    # USER QUERY
    apikey = os.environ['APIKEY']
    hostname = os.environ['HOSTNAME_DYNATRACE']
    # apikey = ''
    # hostname = ''
    userQuery = "SELECT browserMajorVersion FROM usersession"
    api_1 = execQuery(hostname,apikey,userQuery,dt_from,dt_to,verbose)
    
    if api_1 == None:
        sys.exit(1)
    
    if filemode == "csv":
        print("Dumping to csv file")
        api_1.convertPandaToCsv(ouputFilename)
        
    elif filemode == "json":
        print("dumping in json file")
        with open(ouputFilename + ".json", "w") as outfile: 
            json.dump(api_1.resObj, outfile) 
    else:
        print("Output mode not supported!")
        sys.exit(1)
    
    print(api_1.resPanda)
    ## Save end time on file (only in normal mode)
    if (not args.starttime) and (not args.endtime):
        with open('lastTimestamp.json', 'w', encoding='utf-8') as f:
            json.dump(time, f, ensure_ascii=False, indent=4)

    sys.exit(0)
    
    
    
    

def execQuery(hostName,apiToken,userquery,dt_from,dt_to,debug):
    # -- DO NOT CHANGE THE FOLLOWING CODE  -- 
    try:
        api = dynatraceAPIRequests(hostname=hostName,
                           token=apiToken,
                           debug=debug);
    except Exception as e:
        print("Exception: " + str(e))
        return None

    # User session example query
    payload = {}
    query = "query={}&startTimestamp={}&endTimestamp={}&addDeepLinkFields=true&explain=false" \
    .format(urllib.parse.quote(userquery),int(dt_from),int(dt_to))
    parameters = "?" + query
    endpoint = "userSessionQueryLanguage/table" + parameters

    # API Request
    api.request("GET",payload,endpoint)
    if( api.resObj['extrapolationLevel']!=1):
        print('extrapolationLevel is not == 1; so the data will not be complete!')
        
    return api

    
    
class dynatraceAPIRequests:
    def __init__(self,hostname,token,debug):
        self.debug = debug
        self.hostname = hostname
        #self.tenantId = tenantId
        self.apiVersion="v1"
        self.token = token
        self.resObj = ""
        self.resPanda = pd.DataFrame() # pandas DataFrame
        
        
    def request(self,method,payload,endpoint):
        if self.debug: print("ENDPOINT: {}".format(endpoint))
    
        url = 'https://{}/api/{}/{}' \
        .format(self.hostname,self.apiVersion,endpoint)
        if self.debug: print(url)
        #url = "https://fwu26000.live.dynatrace.com/api/v1/userSessionQueryLanguage/table?query=SELECT%20*%20FROM%20usersession&startTimestamp=1582140500&endTimestamp=1582140549&addDeepLinkFields=true&explain=false"
        headers = {
          'Authorization': 'Api-Token ' + self.token,
          'accept': 'application/json'
        }
        
        response = requests.request(method, url, headers=headers, data = payload, verify=False)
        #if self.debug:
        #   print("RESPONSE CONTENT: " + str(response.content))
        self.resObj = response.json()
        # converting json to dataframe pandas 
        d = self.resObj
        self.resPanda = pd.DataFrame(d['values'],columns=d['columnNames'])
        return response
    
    def convertFileJsonToPandas(self,filename):
        try:
          with open(filename,'r') as json_file:
              data = json.load(json_file)
        except Exception as e:
            raise Exception("problem opening json file - " + str(e)) 
        if self.debug:
            print("values entries: "+str(len(data['values'])))
        if(data):
            return self.convertJsonPandas(data)

    def convertPandaToCsv(self,filename, dataframe = None ):
        if dataframe is None:
            dataframe = self.resPanda
        csvfile = filename + ".csv"
        dataframe.to_csv (csvfile, index = False)


    def convertPandaToExcel(self,filename,dataframe,sheetName):
       #Set destination directory to save excel.
       xlsFile = filename + '.xlsx'
       writer = pd.ExcelWriter(xlsFile, engine='xlsxwriter')
       dataframe.to_excel(writer,
                          sheet_name=sheetName)
       workbook = writer.book
       worksheet = writer.sheets[sheetName]
       
       # fixing the length of the columns automatically
       for i, col in enumerate(dataframe.columns):
            # find length of column i
            column_len = dataframe[col].astype(str).str.len().max()
            # Setting the length if the column header is larger
            # than the max column value length
            column_len = max(column_len, len(col)) + 2
            # set the column length
            worksheet.set_column(i, i, column_len)
       writer.save()
       return
        
        

if __name__ == '__main__':
    main()
        