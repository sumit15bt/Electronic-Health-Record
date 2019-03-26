import random
import string
import urllib.parse
import urllib.request



def rand_pass(size):
        # Takes random choices from
	# ascii_letters and digits
	generate_pass = ''.join([random.choice( string.ascii_uppercase +
		                            string.ascii_lowercase +
		                            string.digits)
		                            for n in range(size)])
	return generate_pass

# Driver Code
password = rand_pass(5)

print(password)


authkey = "267368ANbjR9YCbb85c89f6b7" # Your authentication key.

mobiles = "6392741843" # Multiple mobiles numbers separated by comma.

message = "Your OTP  is  {}".format(password) # Your message to send.

sender = "SMSIND" # Sender ID, While using route4 sender id should be 6 characters long.

route = "4" # Define route

# Prepare you post parameters
values = {
'authkey' : authkey,
'mobiles' : mobiles,
'message' : message,
'sender' : sender,
'route' : route
}


url = "http://api.msg91.com/api/sendhttp.php" # API URL

postdata = urllib.parse.urlencode(values).encode('utf-8') # URL encoding the data here.

req = urllib.request.Request(url, postdata)

response = urllib.request.urlopen(req)

output = response.read() # Get Response

print(output) # Print Response

