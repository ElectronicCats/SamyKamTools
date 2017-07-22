from wave import open as openw
from struct import pack
from operator import xor

bits = 7
base = 32
max = 63
padding = 20
frequency = 15
data = filen = None
trackp = None
counterFile = 1

def splitData(data1,track1,padding1,freq1):
    global bits, base, max, padding, frequency, data, filen, trackp, counterFile
    data = data1
    trackp = track1
    padding = padding1
    frequency = freq1
    filen = 'static/audio/'+str(counterFile) + '.wav'
    counterFile = counterFile + 1
    if counterFile > 10:
        counterFile = 1

    if data == '' or data == None:
	return render_template("index.html")
        
    trackp = int(trackp if trackp.isdigit() else 1)
    padding = int(padding if padding.isdigit() else 20)
    frequency = int(frequency if frequency.isdigit() else 15)
    
    if len(data) > 107:
        return render_template("index.html")
    
    if trackp != None:
        if trackp == '2' or trackp == '3':
            bits = 5
            base = 48
            max = 15

    return GenerateWav()
    
def GenerateWav():
    global data, trackp
    detailv = 'Filename: ' + filen + ' - Bits: ' + str(bits) \
    + ' - Max: ' + str(max) + ' - Base: ' + str(base) + ' - Padding: ' + str(padding)[:3] \
    + ' - Frequency: ' + str(frequency)[:3] + ' - Track number: ' + str(trackp)[:1]
    print detailv
    errorv = ''
    zero = ''
    lrc = []
    output = ''
    for x in range(bits):
        zero += "0"
        lrc.append(0)
    
    for x in range(padding):
        output += zero

    for x in range( len(data) ):
        raw = ord(data[x]) - base
        if raw < 0 or raw > max:
	        return render_template("index.html")
            
        parity = 1
        for y in range(bits-1):
            output += str(raw >> y & 1)
            parity += raw >> y & 1
            lrc[y] = xor(lrc[y], raw >> y & 1)
            
        output += chr((parity % 2) + ord('0'))

    parity = 1
    for x in range(bits - 1):
        output += chr(lrc[x] + ord('0'))
        parity += lrc[x]
        
    output += chr((parity % 2) + ord('0'))
    for x in range(padding):
        output += zero
    #Finishing first part of the code:
    
    #Second part:
    #print "Creating wav file: " + filen
    newtrack=openw(filen,"w")
    params= (1, 2, 22050, 0L, 'NONE', 'not compressed')
    newtrack.setparams(params)
    data = output
    peak = 32767
    for x in range(20):
        newtrack.writeframes(pack("h",0))
    # write the actual data
    # square wave for now
    n = 0
    writedata = peak
    while n < len(data):
        if data[n] == '1':
            for x in range(2):
                writedata = -writedata
                for y in range(frequency/4):
                    newtrack.writeframes(pack("h",writedata))

        if data[n] == '0':
            writedata = -writedata
            for y in range(frequency/2):
                newtrack.writeframes(pack("h",writedata))
        n = n + 1
    newtrack.close()
    return filen
