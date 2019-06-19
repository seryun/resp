import serial
import struct
import time
import sqlite3 as lite
import datetime
import requests

TARGET_URL = 'https://notify-api.line.me/api/notify'
TOKEN = 'nmeJMJyjgn6ldKdtLwoMV1firh9uJIWCA8duvUpYrrj'

database_filename = 'test3.db'
conn = lite.connect(database_filename)
cs = conn.cursor()

date = datetime.datetime.now()
t3 = date.strftime('%Y%m%d')
t3 = 'd' +t3

#create table
query = "CREATE TABLE IF NOT EXISTS "+t3+" (name VARCHAR(255), date_time DATETIME PRIMARY_KEY NOT_NULL, rpm INTEGER, distance FLOAT, movement FLOAT, s_quality INTEGER)"
cs.execute(query)
#cs.execute("delete from d20190522 where rpm=54")

XT_START = b"\x7D"
XT_STOP = b"\x7E"
XT_ESCAPE = b"\x7F"

XTS_SPC_APPCOMMAND = b"\x10"
XTS_SPC_MOD_SETMODE = b"\x20"
XTS_SPC_MOD_LOADAPP = b"\x21"
XTS_SPC_MOD_RESET = b"\x22"
XTS_SPC_MOD_SETLEDCONTROL = b"\x24"

XTS_SPR_APPDATA = b"\x50"

#XTS_ID_APP_RESP = b"\x14\x23\xa2\xd6"
#XTS_ID_APP_RESP = b"\xd6\xa2\x23\x14"   # 0x1423A2D6 rearranged to send LSB first
XTS_ID_APP_RESP = b"\xd6\xa2\x23\x14"

#XTS_ID_RESP_STATUS = b"\x23\x75\xfe\x26"
XTS_ID_RESP_STATUS = b"\x26\xfe\x75\x23"
XTS_ID_DETECTION_ZONE =b"\x1c\x0a\xa1\x96" # debug needed 0x96a10a1c

XTS_SM_RUN = b"\x01"
XTS_SM_NORMAL = b"\x10"
XTS_SM_IDLE = b"\x11"

XT_UI_LED_MODE_OFF = b"\x00"
XT_UI_LED_MODE_SIMPLE = b"\x01"
XT_UI_LED_MODE_FULL = b"\x02"

XTS_SPCA_SET = b"\x10"

#State codes:
XTS_VAL_RESP_STATE_BREATHING = "00"   #Valid RPM detected Current RPM value
XTS_VAL_RESP_STATE_MOVEMENT = "01"   #Detects motion, but can not identify breath 0
XTS_VAL_RESP_STATE_MOVEMENT_TRACKING = "02" # Detects motion, possible breathing 0
XTS_VAL_RESP_STATE_NO_MOVEMENT = "03"   #No movement detected 0
XTS_VAL_RESP_STATE_INITIALIZING = "04"   #No movement detected 0
XTS_VAL_RESP_STATE_UNKNOWN = "06"

XTS_SPR_APPDATA_USER = "50"
XTS_ID_APP_RESP_USER = "d6a22314"
XTS_ID_RESP_STATUS_USER = "26fe7523"


def send_command(command):
  # Calculate CRC
  crc_command = XT_START + command
  crc = 0
  #print(crc_command)
  for el in crc_command:
      #print(hex(el))
      crc ^= el ## ord(el)

  #print crc
  #Convert crc to a sendable byte-string-array-thing
  crc_string = struct.pack('!B', crc)

  #Add escape bytes if necessary
  for el in command:
    if (el == b"\x7D" or el == b"\x7E" or el == b"\x7F"):
      print ("Escaping needed but not implemented!")
  
  #Create string to send
  full_command = XT_START + command + crc_string + XT_STOP

  print ("Sending:")
  for el in full_command:
    print ("0x%x" % el) ##ord(el))

  # Send data
  ser.write(full_command)
  
  
def receive_data():
  # Read response
  print ("Receiving...")
  #aaa=list()
  last_char = ''
  response = ''
  while (1):
    #read a byte
    cur_char = ser.read() #Read response from radar

    if len(cur_char)!=0 : 
        print (hex(ord(cur_char)))
    else:
        return response    
    
    #Fill response string
    response += (hex(ord(cur_char)))
    
    if (cur_char == XT_STOP and last_char != XT_ESCAPE):
      break;
    
    #Update last_char
    last_char = cur_char
    
  return response


def get_respiration_data():
  
  resp_data = receive_data()

  #resp_data = list(resp_data)
  resp_list = list()
  
  for i in range(len(resp_data)):
      if resp_data[i] == 'x':
          if i+7<=len(resp_data):
              if resp_data[i+4] == 'x':
                  resp_list.append(resp_data[i+1]+resp_data[i+2])
              else:
                  resp_list.append('0'+resp_data[i+1])
                  
  resp_list.append(resp_data[-2:])
  print(resp_list)   
 
  #Check that it's app-data we've received
  if (resp_list[1] != XTS_SPR_APPDATA_USER):
    print ("Tried to read appdata data from non-appdata packet")
    return
  
  #Check that XTS_ID_RESP_STATUS is correct (just to make sure we are getting the right data)
  xirs = resp_list[2] + resp_list[3] + resp_list[4] + resp_list[5]
  
  if (XTS_ID_RESP_STATUS_USER != xirs):
    print ("XTS_ID_RESP_STATUS not correct")
    
   #Counter value
  counter = resp_list[9] + resp_list[8] + resp_list[7] + resp_list[6]
  counter= int('0x'+counter,16)
  print ("Counter: ", counter)
  print ("")
   
  #State code
  state_code = resp_list[10]
  print("************* " + state_code)
  if state_code == XTS_VAL_RESP_STATE_BREATHING:
    print ("Breathing detected:")
  elif state_code == XTS_VAL_RESP_STATE_MOVEMENT:
    print ("Movement")
    #return
  elif state_code == XTS_VAL_RESP_STATE_MOVEMENT_TRACKING:
    print ("Movement tracking")
    #return
  elif state_code == XTS_VAL_RESP_STATE_NO_MOVEMENT:
    print ("No movement")
    #return
  elif state_code == XTS_VAL_RESP_STATE_INITIALIZING:
    print ("Initializing")
    return
  elif state_code == XTS_VAL_RESP_STATE_UNKNOWN:
    print ("State unknown")
    return
  else:
    print ("Unknown state code!")
    return
  
  print ("")
  
  state_data = resp_list[17] + resp_list[16] + resp_list[15] + resp_list[14]
  state_data = int('0x'+state_data,16)
  print ("RPM: " , state_data)
  
  distance = resp_list[21] + resp_list[20] + resp_list[19] + resp_list[18]
  distance = int('0x'+distance,16)
  distance = distance/10000000000
  print ("Distance: " , distance)
  
  movement = resp_list[25] + resp_list[24] + resp_list[23] + resp_list[22]
  movement = int('0x'+movement,16)
  movement = movement/1000000000
  print ("Movement: " , movement)
  
  sig_quality = resp_list[29] + resp_list[28] + resp_list[27] + resp_list[26]
  sig_quality = int('0x'+sig_quality,16)
  
  print ("Signal quality: " , sig_quality)
  
  print ("")
  
  if state_code == XTS_VAL_RESP_STATE_BREATHING:
      date = datetime.datetime.now()
      date_time= date.strftime('%Y-%m-%d, %H:%M:%S')
      if sig_quality == 10 and state_data>=0 and state_data<=60:
         query = "INSERT into "+t3+" values (?,?,?,?,?,?);"
         cs.execute(query,('Kim',date_time,state_data,distance,movement,sig_quality))
         conn.commit()


#Settings
port_name = 'COM10' ##'/dev/ttyUSB0'
port_speed = 115200

# Connect to (virtual) serial port
ser = serial.Serial(port_name, port_speed, timeout=1, write_timeout=5)   # open serial port
print ("Opened " + ser.portstr)         # Print status to user

time.sleep(2)

## Load respiration app
print ("Load respiration app")
send_command(XTS_SPC_MOD_LOADAPP + XTS_ID_APP_RESP)
receive_data()  #Receives the ackonowledge


# Set detection zone
start_zone = struct.pack("!f", 0.3)
stop_zone = struct.pack("!f", 1.5)
send_command(XTS_SPC_APPCOMMAND + XTS_SPCA_SET + XTS_ID_DETECTION_ZONE + start_zone + stop_zone)
receive_data()

# Execute application
time.sleep(2)
print ("Executing app")
send_command(XTS_SPC_MOD_SETMODE + XTS_SM_RUN)
time.sleep(1.5)
receive_data() #Receives the ackonowledge

print ("Waiting for data")

#Loop forever
while(1):
  time.sleep(0.5)
  get_respiration_data()
  print ("")
  print ("")

#Close serial port    
ser.close()                 
conn.close()