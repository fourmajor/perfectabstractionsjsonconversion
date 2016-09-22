import re
import string
import sys

# simplejson should be in your working directory as specified below
sys.path.append("./json/")
import simplejson as json

# separate the headers from the bodies
format2 = re.split("S([0-9]*)F([0-9]*)\s*\naccept reply: (.*)", \
open("format1.txt", "r").read())

#get rid of extra whitespace, get rid of first line containing "data"
format2 = [item.strip() for item in format2]
format2 = format2[1:]

# each item contains SF code, reply, level, and body, which is four things
# therefore we need to divide total length of format2 by four to get total
# number of items
numitems = len(format2) / 4

listofdicts = list()
i = 0

# now we take our messy list with different data types smooshed together
# and organize it in a list of dictionaries
while i < numitems:
	listofdicts.append({"header":{"stream":format2[i * 4], \
	"function":format2[i * 4 + 1], "reply":format2[i * 4 + 2]}, \
	"body":format2[i * 4 + 3]})
	i += 1

# main workhorse function. nests items based on level ("L#" in format1)
# via some recursive action. Also properly formats the body data based on
# the type of data it is, and renamed variable types.
def createnestedbody(itembody, level):
	i = 0
	newbody = list()
	regexstring = "(?:float|integer|asc|bool).+?(?=(?:float|integer|asc|bool|\Z))"
	while i < len(itembody):
		# the following if/elif/else takes different action depending on if
		# this item is on the current level or not.
		if (int(itembody[i]) == level):
			listofitems = list()
			if len(itembody[i+1]) > 1:
				# splits out the individual body entries based on starting 
				# with keywords, followed by anything (including newlines), 
				# and up to but not including another keyword or end of string
				# re.S allows multiline searching
				for line in re.findall(regexstring, itembody[i+1], \
				re.S | re.IGNORECASE):
					# now that we have individual body entries we have to 
					# split around the commas
					itemsplit = line.split(",")
					
					# depending on the data type we convert differently
					if(itemsplit[0].lower() == "float") :
						itemsplit[0] = "F4"
						itemsplit[1:] = map(float, itemsplit[1:])
					elif(itemsplit[0].lower() == "integer") :
						itemsplit[0] = "U4"
						itemsplit[1:] = map(int, itemsplit[1:])
					elif(itemsplit[0].lower() == "asc") :
						itemsplit[0] = "A"
						
						# strip both newlines and quotes from beginning and end
						# of the strings
						itemsplit[1:] = \
						[string.strip(x, "\"\n") for x in itemsplit[1:]]
					elif(itemsplit[0].lower() == "bool") :
						itemsplit[0] = "Boolean"
						itemsplit[1:] = \
						[(lambda x: "true" in x)(x) for x in itemsplit[1:]]
					
					# if myvalue is only one item long, we make it not a list
					myvalue = itemsplit[1:]
					if(len(myvalue) == 1): myvalue = myvalue[0]
					
					listofitems.append({"format" : itemsplit[0], "value" : myvalue})
			
			# again of the list of format:values is only one, we make it not a 
			# list
			if(len(listofitems) == 1): listofitems = listofitems[0]
			newbody.append(listofitems)
			
			# iterate by two, because in this list one value is the level, 
			# the next is the body
			i += 2
			
		# if the level of this item is higher than our current level, we 
		# return to get to previous recursion level	
		elif (int(itembody[i]) > level):
			return (newbody, i)
		
		# if level is less than current level, we recurse
		else:
			(itemstoappend, iterations) = createnestedbody(itembody[i:], \
			int(itembody[i]))
			newbody.append(itemstoappend)
			i += iterations
	
	# we return i so we know how many items we have gone through, this being
	# a recursive function
	return (newbody, i)

# for each header/body combo	
for item in listofdicts:
	# get the item levels
	item["body"] = re.split("L,([0-9])", item["body"])[1:]
	
	# clean up white space from our bodies
	item["body"] = [x.strip() for x in item["body"]]
	
	# create our nested body
	if(len(item["body"]) > 0):
		(item["body"], trash) = createnestedbody(item["body"],\
		int(item["body"][0]))
	else: item["body"] = list()

# use JSON library to make our output pretty and valid
print json.dumps(listofdicts, indent=4, separators=(',', ': '))