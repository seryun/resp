import serial
import struct

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
#XTS_ID_DETECTION_ZONE =b"\x1c\x0a\xa1\x96" # debug needed 0x96a10a1c

XTS_SM_RUN = b"\x01"
XTS_SM_NORMAL = b"\x10"
XTS_SM_IDLE = b"\x11"


XT_UI_LED_MODE_OFF = b"\x00"
XT_UI_LED_MODE_SIMPLE = b"\x01"
XT_UI_LED_MODE_FULL = b"\x02"

XTS_SPCA_SET = b"\x10"

#State codes:
XTS_VAL_RESP_STATE_BREATHING = 0   #Valid RPM detected Current RPM value
XTS_VAL_RESP_STATE_MOVEMENT = 1   #Detects motion, but can not identify breath 0
XTS_VAL_RESP_STATE_MOVEMENT_TRACKING = 2 # Detects motion, possible breathing 0
XTS_VAL_RESP_STATE_NO_MOVEMENT = 3   #No movement detected 0
XTS_VAL_RESP_STATE_INITIALIZING = 4   #No movement detected 0
XTS_VAL_RESP_STATE_UNKNOWN = 6


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
    response += str(cur_char)
    if (cur_char == XT_STOP and last_char != XT_ESCAPE):
      break;
    
    #Update last_char
    last_char = cur_char
    
  return response


def get_respiration_data():
  resp_data = receive_data()
  
  #Check that it's app-data we've received
  if (resp_data[1] != XTS_SPR_APPDATA):
    print ("Tried to read appdata data from non-appdata packet")
    return
  
  #Check that XTS_ID_RESP_STATUS is correct (just to make sure we are getting the right data)
  xirs = resp_data[5] + resp_data[4] + resp_data[3] + resp_data[2]
  if (XTS_ID_RESP_STATUS != xirs):
    print ("XTS_ID_RESP_STATUS not correct")
    
    #Debug information
    print ("Received XTS_ID_RESP_STATUS:")
    print (hex(struct.unpack("<i", str(xirs))[0]))
    print ("Should be:")
    print (hex(struct.unpack("<i", str(XTS_ID_RESP_STATUS))[0]))
    return
  
  #Counter value
  counter = struct.unpack("<i", str(resp_data[6:10]))[0]
  print ("Counter: " + str(counter))
  print ("")
  
  #State code
  state_code = struct.unpack("B", str(resp_data[10]))[0]
  
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
  
  state_data = struct.unpack("<i", str(resp_data[14:18]))[0]
  print ("RPM: " + str(state_data))
  
  distance = struct.unpack("<f", str(resp_data[18:22]))[0]
  print ("Distance: " + str(distance))
  
  movement = struct.unpack("<f", str(resp_data[22:26]))[0]
  print ("Movement: " + str(movement))
  
  sig_quality = struct.unpack("<i", str(resp_data[26:30]))[0]
  print ("Signal quality: " + str(sig_quality))
  
  print ("")


#Settings
port_name = 'COM10' ##'/dev/ttyUSB0'
port_speed = 115200

# Connect to (virtual) serial port
ser = serial.Serial(port_name, port_speed, timeout=1, write_timeout=5)   # open serial port
print ("Opened " + ser.portstr)         # Print status to user
    
## RESET MODULE
print ("Resetting module")
send_command(XTS_SPC_MOD_RESET)
receive_data()  #Receives the "booting" state

#Close serial port    
ser.close()                 # close port
