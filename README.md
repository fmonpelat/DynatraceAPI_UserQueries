# DynatraceAPI_UserQueries
Dynatrace API Requests Script helper for User Session queries

To use the script we must configure the environment variables. 
If we are using spyder from anaconda, the steps are:
Preferences -> Ipython Console -> Startup
Insert in Run code in the lines box insert:
import os; os.environ['APIKEY']='<api key>';os.environ['HOSTNAME_DYNATRACE']='<host name>'
  
if not from console, export the variables:
export APIKEY='<api key>'
export HOSTNAME_DYNATRACE='<host name>'
