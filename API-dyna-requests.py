#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 15:43:30 2020

@author: fmonpelat

MIT License

Copyright (c) [2020] [Facundo Monpelat]

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
import time
import requests
import urllib.parse
import datetime
import json
import os
import pandas as pd




def main():

    # environment variables token key and dynatrace hostname
    apiToken = os.environ['APIKEY']
    hostName = os.environ['HOSTNAME_DYNATRACE']
    try:
        api = dynatraceAPIRequests(hostname=hostName,
                           token=apiToken,
                           debug=1);
    except Exception as e:
        print("Exception: " + str(e))
        return
        
    # ONLY CHANGE THIS VARIABLES 
    # USER QUERY
    userQuery = "SELECT * FROM usersession"
    # TIMEFRAMES
    utc_date_str_from = '2020-02-19 11:44'
    utc_date_str_to = '2020-02-20 11:44'   
 
    
    convertFiles(api)
    return
    
    # DO NOT CHANGE THE FOLLOWING CODE 
    
    # format year-month-day hour:minutes
    #utc_date_str_from = '2020-02-18 00:00'
    dt = datetime.datetime.strptime(utc_date_str_from, '%Y-%m-%d %H:%M')
    dt_from = int((dt.timestamp()* 1000))
    
    #utc_date_str_to = '2020-02-20 11:44'   
    dt = datetime.datetime.strptime(utc_date_str_to, '%Y-%m-%d %H:%M')
    dt_to = int((dt.timestamp()* 1000))
    
    # User session example query
    payload = {}
    query = "query={}&startTimestamp={}&endTimestamp={}&addDeepLinkFields=true&explain=false" \
    .format(urllib.parse.quote(userQuery),int(dt_from),int(dt_to))
    parameters = "?" + query
    endpoint = "userSessionQueryLanguage/table" + parameters

    # API Request
    res = api.request("GET",payload,endpoint);
    resObj = res.json()
    if( resObj['extrapolationLevel']!=1):
        print('extrapolationLevel is not == 1; so the data will not be complete!')
    
    # Formatting response and export to excel from pandas dataframe
    dframe = api.convertJsonPandas(resObj)
    api.convertPandaToExcel("userQuery",dframe,"User Session Query")
    print(dframe)

    
def convertFiles(api):
    dFrame1 = api.convertFileJsonToPandas("data/response_1582143216942.json")
    dFrame2 = api.convertFileJsonToPandas("data/response_1582143341055.json")
    api.convertPandaToExcel("data/userQuery1-(response_1582143216942.json)",dFrame1,"User Session Query 1")
    api.convertPandaToExcel("data/userQuery2-(response_1582143341055.json)",dFrame2,"User Session Query 2")

    
    
class dynatraceAPIRequests:
    def __init__(self,hostname,token,debug):
        self.debug = debug
        self.hostname = hostname
        #self.tenantId = tenantId
        self.apiVersion="v1"
        self.token = token
        
        
    def request(self,method,payload,endpoint):
        if self.debug:
            print("ENDPOINT: {}".format(endpoint))
    
        url = 'https://{}/api/{}/{}' \
        .format(self.hostname,self.apiVersion,endpoint)
        print(url)
        #url = "https://fwu26000.live.dynatrace.com/api/v1/userSessionQueryLanguage/table?query=SELECT%20*%20FROM%20usersession&startTimestamp=1582140500&endTimestamp=1582140549&addDeepLinkFields=true&explain=false"
        headers = {
          'Authorization': 'Api-Token ' + self.token,
          'accept': 'application/json'
        }
        
        response = requests.request(method, url, headers=headers, data = payload)
        if self.debug:
            print("RESPONSE CONTENT: " + str(response.content))
        return response 
    
    def convertJsonPandas(self,jsonObj):
        d = jsonObj
        df = pd.DataFrame(d['values'],columns=d['columnNames'])
        return df
    
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
        