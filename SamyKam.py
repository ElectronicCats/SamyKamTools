"""'
SamyKam - A set of pentesting tools to test Mag-Stripe readers and tokenization processes

Code and hardware integration by Salvador Mendoza (https://salmg.net)
PCB design and advisory by Andres Sabas
Team work with @electronicats (https://twitter.com/electronicats)

Named the tool in honor of Samy Kamkar(http://samy.pl)
For his hard work and community support
 
It is a MagSpoof but specfically designed for Raspberry Pi:
- OLED for prepared attacks
- Rotary endoder for navigation menu

Support:
Mini-shell for basic commands implementing Bluetooth and Webserver independently
- change parameters without ssh
- change wifi configuration [ssid/pass] *
- send any shell command using Bluetooth

"""
from flask import Flask, request, json, redirect, render_template, escape
from gaugette import rotary_encoder, switch, gpio
from threading import Thread
from subprocess import PIPE, call, Popen
from shlex import split as split1
from os import path, environ, chdir
from urllib2 import urlopen
from Adafruit_SSD1306 import SSD1306_128_32
from time import sleep
from PIL import Image, ImageDraw, ImageFont
from bluetooth import *

webPort = 5002 #WebServer port

MAGPIN = 7
WAITINTRO = 2

RST = 24
SLARGO = 120
MANCHO = 10
MINIT = 0

#Rotary Encoder configuration pins 
A_PIN  = 15 #7 - board 8
B_PIN  = 16 #9 - board 10
SW_PIN = 4  #8 - board 16
#GND - board 6
#GND - board 9

#OLED 
# - SDA -> board 2
# - SCL -> board 5
# - VCC -> board 1
# - GND -> board 9
disp = SSD1306_128_32(rst=RST, i2c_bus=1)
disp.begin()
width = disp.width
height = disp.height

# Get drawing object to draw on image.
padding = 2
shape_width = 20
top = padding
bottom = height-padding
x = padding + 3
font = ImageFont.load_default()

#Start encoder configuration
gpio = gpio.GPIO()
encoder = rotary_encoder.RotaryEncoder.Worker(gpio, A_PIN, B_PIN)
encoder.start()
switch1 = switch.Switch(gpio, SW_PIN)
last_state = None

#MagSpoof variables
countTracks = 2
headMFile = '/static/headMagSpoofPI' #Name of top file
tailMFile = '/static/tailMagSpoofPI' #Name of tail file
headMGPI = ''
tailMGPI = ''

#Menus and window configuration
topLevel = top + 19
whereI = 0 #Helps to draw in specific position 
counter = 0 # In charge to keep track of the menus
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)

def getcwd(): #Get script directory
	return  path.dirname(path.realpath("__file__"))


#Flask - webserver functions
app = Flask(__name__)
tracks = {}
statusBluetooth = "Off"
statusWebserver = "Off"
jsonFile = getcwd() + "/static/SamyKam.json"

# Reading data back
def writeTrack(jsonTracks):
    with open(jsonFile, 'w') as f:
        json.dump(jsonTracks, f)
            
def loadTracks():
    global tracks, statusBluetooth, statusWebserver
    if (path.exists(jsonFile)):
        with open(jsonFile, 'r') as f:
            tracks = json.load(f)
    else:
        tracks['track1'] = '%B123456781234567^LASTNAME/FIRST^YYMMSSSDDDDDDDDDDDDDDDDDDDDDDDDD?'
        tracks['track2'] = ';123456781234567=11112220000000000000?'
    if 'bluetooth' in tracks:
        statusBluetooth = tracks['bluetooth']
    else:
        tracks['bluetooth'] = statusBluetooth
    if 'webserver' in tracks:
        statusWebserver = tracks['webserver']
    else:
        tracks['webserver'] = statusWebserver
    writeTrack(tracks)

def linkHome():
    return '</br></br><a href="/">Home</a>'

def jsonValues(args1, manyTracks, toDo):
    global tracks, countTracks
    #data = {}
    tracks['bluetooth'] = statusBluetooth
    if toDo == 0:
        countTracks = 0
        if any("track" in s for s in args1):
            for i in range(1,manyTracks):
                trackGet = "track"+str(i)
                if trackGet in args1:
                    trackValue = args1["track"+str(i)]
                    if len(trackValue) > 0:
                        countTracks += 1
                        tracks[trackGet] = trackValue
    elif toDo == 1:
        for i in range(1,manyTracks):
            trackGet = "track"+str(i)
            if trackGet in tracks:
                tracks.update({trackGet : ""})
        countTracks = 0
    return tracks

@app.route('/cleartracks')
def cleartracks():
    a = jsonValues("", 11, 1)
    writeTrack(a)
    return "Cleared: " + json.dumps(a) + linkHome()


cardsMenu = ["Previous Menu?"]
cardsPlay = []
def formatTracks(): #Generate tracks to compile
    global cardsMenu, cardsPlay
    cardsPlay = []
    allTracks = ''
    #print tracks
    for t1, v1 in tracks.items():
        if len(v1) > 0 and 'track' in t1:
            if len(allTracks) > 0:
                allTracks = allTracks + ','
            allTracks = allTracks + '\n"' + v1 + '\\0"'
            wformat = v1.encode("utf-8")
            cardsMenu.extend(['"' + wformat + '\\0"'])
            cardsPlay.extend([wformat])
    return allTracks

@app.route('/')
def api_root():
    loadTracks()
    #print tracks
    web = """SamyKam Web Commands:<br/><br/><a href="/magspoof">Run MagSpoof</a>
    <br/><a href="compile">Compile MagSpoof</a>
    <br/><a href="cleartracks">Clear tracks</a></br>
    </br><form action = "/addtracks" method = "POST">Change Tracks:"""
    inputs = ''
    for i in range(1,11):
        t1 = tracks['track'+str(i)] if ('track' + str(i)) in tracks else ''
        inputs = inputs + '<input type="text" class="pure-input-1" placeholder="Track" name="track'+str(i)+'" value="' + t1 +'"/>'
    
    #inputs = inputs + '<p>Track '+ str(i) + ': <input type = "text" name = "track'+str(i)+'" size="66" value="' + t1 +'"/></p>'
    #inputs = inputs + '<p><input type = "submit" value = "submit" /></p></form>'    
    checkBlue = 'Activate ' if statusBluetooth == 'Off' else 'Deactivate'
    #inputs += '<br/><a href="bluetooth">'+ checkBlue + ' Bluetooth</a>'
    return render_template("index.html", tracksv=inputs)
    
#Adding BlueSpoof Support - Beta version
@app.route('/playthem', methods = ['POST']) #Adding BlueSpoof Support
def playBluespoof():
    result = request.form if request.method == 'POST' else request.args
    checkRequest = jsonValues(result, 11, 0)
    formatPlay = formatTracks()
    for i in range(0,len(cardsPlay)):
    	prepareWav(cardsPlay[i], '1')
    return redirect("/", code=302)
    
@app.route('/bluespoof')
def webBluespoof():
    loadTracks()
    inputs = ''
    for i in range(1,11):
        t1 = tracks['track'+str(i)] if ('track' + str(i)) in tracks else ''
        inputs = inputs + '<textarea class="pure-input-1" placeholder="%4929555123456789^MALFUNCTION/MAJOR ^0902201010000000000000970000000?" name="track'+str(i)+'"/>'+t1+'</textarea>'
        #inputs = inputs + '<input type="text" class="pure-input-1" placeholder="Track" name="track'+str(i)+'" value="' + t1 +'"/>' 
        
    #runBluespoof()
    return render_template("bluespoof.html", tracksv=Markup(inputs))
#--BlueSpoof beta code

@app.route('/bluetooth')
def webBluetooth():
    runBluetooth()
    return 'Updated Bluetooth status!' + linkHome()

@app.route('/magspoof')
def webMagspoof():
    runMagspoof()
    return 'Done sending mag-stripe!'+linkHome()

@app.route('/compile')
def webMakespoof():
    genMakefile()
    return 'Compiled MagSpoof! enjoy...'+linkHome()

@app.route('/addtracks', methods = ['POST', 'GET'])
def webTracks():
    result = request.form if request.method == 'POST' else request.args
    checkRequest = jsonValues(result, 11, 0)
    
    # Writing JSON data
    writeTrack(checkRequest)
    return 'Added tracks: ' + json.dumps(checkRequest) + linkHome()

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def shutWeb(): #shutdown using a request from the script
	response = urlopen('http://0.0.0.0:' + str(webPort) + '/shutdown')
	html = response.read()
	print html    

@app.route('/shutdown')
def shutdown():
    global statusWebserver
    statusWebserver = "Off"
    shutdown_server()
    return 'Shutting down...'

#-End WebServer
        
def selectMenu(wayGo): #Where to draw a selection
	global whereI
	if (wayGo >= 0):
		draw.rectangle((MINIT, topLevel, SLARGO, MANCHO), outline=255, fill=0)
		whereI = 0
	elif(wayGo < 0):
        	draw.rectangle((MINIT, topLevel, SLARGO, MANCHO+20), outline=255, fill=0)
        	whereI = 1

def clearDisplay(): #Reset display
        disp.clear()
        disp.display()
        draw.rectangle((0,0,width,height), outline=0, fill=0)

clearDisplay()

if (path.exists(getcwd() + '/static/samy.ppm')):
	image2 = Image.open(getcwd() + '/static/samy.ppm').resize((width, height), Image.ANTIALIAS).convert('1')
	draw2 = ImageDraw.Draw(image2)
	font2 = ImageFont.truetype(getcwd() + '/static/3dventure.ttf', 20)
	draw2.text((x, height-12), "SamyKam",font=font2, fill=255)
	disp.image(image2)
	disp.display()
	sleep(WAITINTRO)

def genFunctions(d1): #Bluetooth commands handler 
    splitData = d1.lower() 
    splitData = splitData.split()
    if (splitData[0] == "run"):
        runMagspoof()
        return("Running MagSpoof...\n")
    elif (splitData[0] == "compile"):
        genMakefile()
        return("Compiling MagSpoof...\n")
    elif (splitData[0] == "clear"):
        tracks = ''
        return("Cleared tracks\n")
    elif ('track' in splitData[0]):
        if (len(splitData) == 2):
            #addTrack(splitData[1])
    	    checkRequest = jsonValues({splitData[0] : splitData[1]}, 11, 0)
 	    #print checkRequest
            writeTrack(checkRequest)
            return("Adding track: " + d1 + "\n")
        else:
            return("Error: add track data\n")
    elif (splitData[0] == "wifi"):
        if (len(splitData) == 2):
            changeWifi(d1)
            return("Changing WiFi configuration to : " + d1 + "\n")
        else:
            return("Error: parameters\n")
    elif (d1 == "quit"):
            return ""
    elif (splitData[0] == "help"):
        return("Commands:\nRun - Run MagSpoof\Track[1-10] [track data] - Add MagSpoof track\nAny Command - Execute any command in the shell\nClear - Clear all the MagSpoof tracks in memory to add new ones\nWifi [SSID] [password] - Add wifi configuration\n")
    else:
	cmd1 = runCommandlog(d1)
	return cmd1 + "\n"

def runBluetooth(): #Bluetooth - make bluetooth discoverable
    global statusBluetooth
    clearDisplay()
    if statusBluetooth == "On":
        statusBluetooth = "Off"
        drawText(0,9,"Stopping->Bluetooth...")
        makep = runCommand('sudo hciconfig hci0 noscan')
        sleep(3)
    else:
        statusBluetooth = "On"
        drawText(0,9,"Running->Bluetooth...")
        makep = runCommand('sudo hciconfig hci0 piscan')
        sleep(2)
        drawText(0,18,"Creating thread...")
        sleep(3)
        blueT = Thread(target=runBluetooth2) # Create a thread
        blueT.start() # In background
    #statusBluetooth = "On" if statusBluetooth == "Off" else "Off"
    tracks['bluetooth'] = statusBluetooth
    writeTrack(tracks)
    menuInit(activeMenu, 0, 0)
    
def runBluetooth2(): #Bluetooth socket handler
    global tracks
    server_sock=BluetoothSocket( RFCOMM )
    server_sock.bind(("",PORT_ANY))
    server_sock.listen(1)
    advertise_service(server_sock, "SamyKam",
                         service_classes=[SERIAL_PORT_CLASS],
                         profiles=[SERIAL_PORT_PROFILE])

    client_sock, address = server_sock.accept()
    print "Accepted connection from ",address
    client_sock.send("Welcome to SamyKam Bluetooth terminal\n\n")
    while 1:
        data = str(client_sock.recv(1024))
        doThings = "Error"
        if data:    
            print "received [%s]" % data
        try:
            doThings = genFunctions(data)
        except: 
            pass
        
        if (doThings == ""):
            break
        else:
            client_sock.send(str(doThings))
        
    client_sock.close()
    server_sock.close()

def runCommand(command): #Special commands 
    chdir(getcwd())
    run = call(command, shell=True, stdout=PIPE)

def runCommandlog(command): #Mini-shell handler 
    p = Popen(split1(command), stdout=PIPE)
    result = p.communicate()[0].strip()
    return result

def changeWifi(id2): #Basic wifi configuration
    splitWifi = id2.split()
    id1 = splitWifi[0]
    lenWifi = len(splitWifi)
    pass1 = ""
    if (lenWifi >= 2):
        pass1 = splitWifi[len(splitWifi)-1]
    lenPass = len(pass1)
    if (lenPass > 0):
        id1 = id2[:-(lenPass+1)]
    id1 = '"' + id1 + '"'
    pass1 = '"' + pass1 + '"'
    tmpFile = """
        auto lo

        iface lo inet loopback
        iface eth0 inet dhcp

        allow-hotplug wlan0
        auto wlan0

        iface wlan0 inet dhcp
                wpa-ssid """ + id1 + """
                wpa-psk """ + pass1 + """
        """
    
def addNtracks(): #MagSpoof tracks #s
    n1 = countTracks
    return "#define TRACKS " + str(n1) + ';\nconst char* tracks[] = {'

#"%B123456781234567^LASTNAME/FIRST^YYMMSSSDDDDDDDDDDDDDDDDDDDDDDDDD?\0", // Track 1 - 66
#";123456781234567=11112220000000000000?\0" // Track 2
def runMagspoof(): #MagSpoof
    clearDisplay()
    drawText(0,18,"Running MagSpoof...")
    makep = runCommand('sudo python ' + getcwd() + '/static/runMagSpoof.py')
    sleep(2)
    menuInit(activeMenu, 0, 0)

cardOr = ''
def makeMagspoof(): #MagSpoof compiler
    headf = getcwd() + headMFile
    tailf = getcwd() + tailMFile
    if (path.exists(headf) and path.exists(tailf)):
        global headMGPI, tailMGPI
        with open(headf,'r') as f:
            headMGPI = f.read()
        with open(tailf,'r') as f:
            tailMGPI = f.read()
        filem = open(getcwd() + '/MagSpoofPI.c', 'w')
        tTrack = ''

        if cardOr == '':
            tTrack = headMGPI + addNtracks() + formatTracks() + tailMGPI
        else:
            tTrack = headMGPI + addNtracks() + one + tailMGPI
        #count = count == N ? 0 : count + 1;

        filem.write(tTrack)
        filem.close()
        clearDisplay()
        drawText(0,18,"Compiling MagSpoof...")
        makep = runCommand('make install')
    else:
        return "No config files"
    menuInit(activeMenu, 0, 0)
    
def genMakefile(): #MagSpoof generator
    global cardOr
    print "------------\nGenerating MagSpoofPI.c:"
    cardOr = ''
    makeIns = Thread(target=makeMagspoof) # Create a thread
    makeIns.start()
    makeIns.join() # Wait until finished

#if __name__ == '__main__':
# Bind to PORT if defined, otherwise default to 5000.
def webDeamon():
    port = int(environ.get('PORT', webPort))
    app.run(host='0.0.0.0', port=port)

def runWebserver():
    global statusWebserver, tracks
    clearDisplay()
    if statusWebserver == "On":
        statusWebserver = "Off"
        drawText(0,9,"Stopping->Webserver...")
        a = shutWeb()
        sleep(3)
    else:
        statusWebserver = "On"
        drawText(0,9,"Running->Webserver...")
        webThread = Thread(target=webDeamon) # Create main thread
        t = webThread.start() # In background
        sleep(2)
        
    tracks['webserver'] = statusWebserver
    writeTrack(tracks)
    menuInit(activeMenu, 0, 0)
    #print "Salio"

def cardsMemory():
    global activeMenu
    formatTracks()    
    activeMenu = cardsMenu
    
listTodo = {
    0 : runMagspoof,
    1 : genMakefile,
    2 : runBluetooth,
    3 : runWebserver,
    4 : cardsMemory,
}

def drawText(x2,y2,text): #Helps to draw a text in a specific position
    draw.text((x2,y2), text, font=font, fill=255)
    disp.image(image)
    disp.display()

fromw = 0 #Handles the len of menus
def menuInit(menuName, wayGo, menuMain):
    global fromw, counter
    top2 = padding
    lenMenu = len(menuName)
    if (wayGo < 0): #Foward scrolling
        if (counter < lenMenu):
            counter += 1
        if (whereI == 1):
            fromw += 1
            if (fromw > lenMenu):
                fromw = lenMenu-1
    elif (wayGo > 0): #Backward scrolling
        if (counter > 0):
            counter -= 1
        if (whereI == 0):
            if (fromw > 0):
                fromw -= 1
    clearDisplay()				
    selectMenu(wayGo)
    drawText(x,top,menuTop[menuMain])
    top2 += 9
    for i in range(fromw,lenMenu):
        drawText(x,top2,menuName[i])
        top2 += 9
        disp.image(image)
        disp.display()

def compileCard(num):
    global countTracks, cardOr
    cardOr = '10'
    countTracks = 1
    print cardsMenu[num]
    #makeMagspoof(cardsMenu[num])
    cardOr = ''

# Menu control
menuTop = ["SamyKam", " ", " "," ","Update"]
menuList1 = ["Run","Make MagSpoof","Bluetooth","WebServer","Cards"]
#cardsMenu = ["Back?"]


activeMenu = menuList1
activeTitle = 0
previousMenu = menuList1
menuInit(activeMenu, 0, 0)
def menuFlow(delta1): #where to go!
	global counter, fromw
        if (delta1 < 0): #Going foward
            if (counter < len(activeMenu) - 1): #Avoiding blank spaces
                menuInit(activeMenu, delta1, activeTitle)
            else: #If is it the end of menu, start in the beginning
                fromw = 0
                counter = 0
                menuInit(activeMenu, 0, activeTitle)
        elif(delta1 > 0): #Going back
            if (counter > 0): #Avoiding black spaces
                menuInit(activeMenu, delta1, activeTitle)
            else: #if is not more menu items, starts at the end
                counter = len(activeMenu) - 1
                fromw = len(activeMenu) - 1
                menuInit(activeMenu, 0, activeTitle)

def mainWhile():
    global sw_state, last_state, counter, fromw, activeMenu
    while 1:
        #Negative value in the encoder means foward in the menu!
        delta = encoder.get_steps()
        if (delta != 0): #Slowing down the encoder data, necessary to have a good scrolling
            sleep(0.2)
        delta = encoder.get_steps()
        if (delta != 0):
            menuFlow(delta)
            print "rotate %d" % delta
            #sleep(0.1)
        
        sw_state = switch1.get_state()
        if sw_state != last_state: 
            print "estate %d" % sw_state
        if (sw_state == 1) and (activeMenu == menuList1): #Pressed the encoder?
            listTodo[counter]() #Depending where is the position in the menu is the action in the listTodo function
            counter = 0
            fromw = 0
            menuInit(activeMenu, 0, activeTitle)
            loadTracks()
            sleep(2)
        elif (sw_state == 1) and (activeMenu == cardsMenu):
            if (counter == 0):
                fromw = 0
                activeMenu = menuList1
                menuInit(activeMenu, 0, activeTitle)
                loadTracks()
                #sleep(1)
            else:
                compileCard(counter)
                sleep(1)
        last_state = sw_state

mainThread = Thread(target=mainWhile) # Create main thread
a = mainThread.start() # In background

loadTracks()
if statusBluetooth == 'On':
        statusBluetooth = 'Off'
        runBluetooth()
if statusWebserver == 'On':
        statusWebserver = 'Off'
        runWebserver()
