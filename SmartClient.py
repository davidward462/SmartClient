# David Ward
# V00920409
# CSC 361, Assignment 1 
# January 28th, 2022

from socket import * # Removes the need to write socket.socket, etc.
import string
import sys
import ssl
import re # Regex

# Program only takes one argument when it is run. (for now)
def checkArgs():
	if not (len(sys.argv)==2):
		sys.exit("Incorrect number of arguments.")
		
		
	# Establish connection with host.
	# Throw exepction and end program if there is a problem.
def makeConnection(s, a, p):
	try:
		s.connect((a, p))
	except Exception as e: 	
		print("Something is wrong with %s:%d. Exception: %s." % (a,p,e))
		sys.exit("Program ended.")
	return s


	# Send http request.
	# Use https because it reduces redirects and simplifies code.
def sendRequest(s, a, hasPath, path):
	print("\n---Request begin---")
	msg = "GET" + " https://" + a + "/"
	if hasPath:
		msg = msg + path
	msg = msg + " HTTP/1.1" + "\r\n"
	#msg = "GET" + " https://" + a + path + " " + "HTTP/1.1" + "\r\n"
	extra = "Host:" + a + "\r\n\r\n"
	newMsg = msg + extra
	print(newMsg)
	s.send(newMsg.encode('utf-8')) # Encode message and send
	print("\n---Request end---\nHTTP request sent, awaiting response...\n")
	
	
	# Get response from server, decode, and return it.
	# Buffer size is too small for some sites, so it does it twice.
	# Still does not work on www.instagram.com
def getResponse(s): 
	bufferSize = 10000
	data = s.recv(bufferSize) # Get response
	data = data + s.recv(bufferSize)
	data = data.decode() # For readability
	return data
	
	
	# Split http response into header and body, and store in a list.
	# Exit program if a blank line cannot be found. (maybe change later)
def splitResponseHeaderAndBody(data):
	splitData = data.split("\r\n\r\n", 1)
	if(len(splitData) != 2):
		print("\nlength:",len(splitData))
		sys.exit("Problem with HTTP response format.")
	header = splitData[0]
	body = splitData[1]
	return header, body
	
	
	# Split input on newline and return.
def seperateIntoList(input):
	splitInput = input.split("\n")
	return splitInput
	
	
	# Gets the head of the http response message, in the form of a list.
	# Returns the status code found on the first line.
def getStatusCode(input):
	found = re.search("\d\d\d", input[0]) # Get HTTP code from just first line.
	if found != None:
		statusCode = found.group()
	else:
		sys.exit("HTTP status code not found.")
	return statusCode
	
	
def getRedirectAddress(input):
	redirectAddress = []
	length = len(input)
	for i in range(length):
		foundAddress = re.match("Location: ", input[i])
		if foundAddress != None:
			end = foundAddress.end()
			redirectAddress.append((input[i])[end:])
	return redirectAddress
	
	
def getCookies(input):
	cookieList = []
	length = len(input)
	for i in range(length):
		foundCookie = re.match("Set-Cookie: ", input[i])
		if foundCookie != None:
			end = foundCookie.end()
			cookieList.append((input[i])[end:])
	return cookieList


def checkHttp2():
	http2 = False
	address = sys.argv[1]
	context = ssl.SSLContext()
	conn = context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname=address)
	context.set_alpn_protocols(['h2'])
	conn.connect((address, 443))
	rawMsg = "GET https://" + address + "/" + " HTTP/1.1\r\nHost:" + address + "\r\n\r\n"
	msg = rawMsg.encode('UTF-8')
	conn.send(msg)
	rawData = conn.recv(2048)
	
	try:
		data = rawData.decode('UTF-8')
	except UnicodeDecodeError:
		return True
		
	hex = re.match("\x00", data)
	
	if hex != None:
		http2 = True
		
	conn.close()
	return http2



	# Print head and body of http response
def printResponse(head, body):
	print("--- Response header ---")
	print(head, end="\n\n")
#	print("--- Response body ---")
#	print(body, end="\n")
	
	# Required output
def printData(address, cookieList, passwordProtected, http2Support):
	print("\n--- Output ---")
	print("website: ", address) #  Might not be correct if there is a redirect
	
	if http2Support:
		print("1. Supports http2: yes")
	else:
		print("1. Supports http2: no")
	
	print("2. List of cookies: ")
	for i in range(len(cookieList)):
		print("Cookie name:",cookieList[i])
	
	if passwordProtected:
		print("3. Password-protected: yes")
	else:
		print("3. Password-protected: no")
	

def main():
	
	# Initialize some variables.
	redirectCount = 0
	requestSuccessful = False
	passwordProtected = False
	http2Support = False
	hasPath = False
	path = ""
	redirectAddress = ""
	
	checkArgs()
	
	argument = sys.argv[1]
	addressList = argument.split("/", 1)
	address = addressList[0]
	if len(addressList)==2:	
		hasPath = True
		path = addressList[1]
	port = 443
	
	
	
	# Main functions
	while (requestSuccessful == False) and (redirectCount < 3):
	
		# Create socket.
		# Wrap with ssl so https works.
		context = ssl.SSLContext()
		ssl_socket = context.wrap_socket(socket(AF_INET, SOCK_STREAM))
		
		makeConnection(ssl_socket, address, port)
		sendRequest(ssl_socket, address, hasPath, path)
		data = getResponse(ssl_socket)
		
		head,body = splitResponseHeaderAndBody(data)
		printResponse(head,body)
		splitData = seperateIntoList(head)
		
		statusCode = int(getStatusCode(splitData))
		
		if (statusCode > 299) and (statusCode < 400): # Redirect
			redirectAddress = getRedirectAddress(splitData)
			if redirectAddress == None:
				sys.exit("Redirect failed.")
		elif(statusCode == 401):
			# Page is password-protected
			requestSuccessful = True
			passwordProtected = True
			cookieList = getCookies(splitData)
			printData(address, cookieList, passwordProtected, False)
			sys.exit()
		elif (statusCode > 199) and (statusCode < 300):
			requestSuccessful = True
			cookieList = getCookies(splitData)
			http2Support = checkHttp2()
			printData(address, cookieList, passwordProtected, http2Support)
			
		address = redirectAddress
		path = ""
		redirectCount = redirectCount + 1
	
		ssl_socket.close()
		
main()