import argparse
import time
import datetime as dt
from datetime import datetime
from dateutil.tz import gettz
from dateutil.parser import parse
import calendar
import requests
import json
import hashlib
from tqdm import tqdm

import mmap

def get_num_lines(file_path):
    fp = open(file_path, "r+")
    buf = mmap.mmap(fp.fileno(), 0)
    lines = 0
    while buf.readline():
        lines += 1
    return lines

def isANumber(string):
  try:
    i = int(string)
  except (ValueError, TypeError):
    try:
      i = float(string)
    except (ValueError, TypeError):
      return False

  return True

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--api_secret', help="API-SECRET for uploading", required=True)
parser.add_argument('--base_url', help="Base URL of site", required=True)
parser.add_argument('--noninteractive', default=False, action='store_true')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--timezone', default=gettz( ), type=gettz, help="Timezone to use.")
parser.add_argument('--mmol', help="Data entered as mmol", action='store_true')
parser.add_argument('--inp', help="Input file from glucometerutils", required=True)
#parser.add_argument('--data_type', choices=['sgv', 'cal'],default="sgv")
args = parser.parse_args()

hashed_secret = hashlib.sha1(args.api_secret.encode('utf-8')).hexdigest()

url = "%s/api/v1/entries" % args.base_url

last_date = ' '



try:
    f= open("last_date.conf","r+")
except IOError:
    # If not exists, create the file
    f= open("last_date.conf","w+")

last_date_check = f.readline().rstrip()
cnt=1
headers = {'API-SECRET' : hashed_secret,
     'Content-Type': "application/json",
     'Accept': 'application/json'}
with open(args.inp) as filer:
    while last_date_check not in filer.readline():
        cnt = cnt+1 #count the number of lines ommited
        continue
    for line in tqdm(filer,total=get_num_lines(args.inp)-cnt):
        line = line.translate({ord(c): None for c in '"()'})
        line_array = line.split(",")
        last_date = line_array[0] # get last line
        #get time fixed
        date_obj = datetime.strptime(line_array[0], "%Y-%m-%d %H:%M:%S")
        #date_obj = date_obj + dt.timedelta(minutes=23) time offset implement in args
        milli_epoch = int(date_obj.strftime("%s")) * 1000
        date_string = date_obj.replace(tzinfo=args.timezone).isoformat()
        #print (date_string)
        #print (milli_epoch)
        #get bg value
        bg = int(float(line_array[1]))
        #print (bg)
        payload = dict(type='sgv', sgv=bg, date=milli_epoch, dateString=date_string)
        #print (date_string)
        if args.debug:
          print ("%s\n" % payload)


        r = requests.post(url, headers=headers, data=json.dumps(payload))
        if (r.status_code == 200):
            continue;
        else:
          print ("%d" % r.status_code)
          print (r.text)

if last_date==' ':
    pass
else:
    f.seek(0)
    f.truncate() #erase last date after getting the string
    f.write(last_date)
