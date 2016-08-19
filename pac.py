import sys
from lib.confParser import load

servers = list()
routers = list()
policies = list()

try:
	elements=load(open(sys.argv[1]))
except: 
	print("usage: " + sys.argv[0] + " <configuration>")
	exit(1)

for element in elements:
	elementType = element[0]
	if type(elementType) is list:
		elementType = elementType[0]
		if elementType == "rules":
			try:
				policy_block=element[1]
				policy_name=element[0][1]
				pGroup=[policy_name]
				pItem=list()
				for policy in policy_block:
					policyType=policy[0]
					policyValue=policy[1].replace('"', '').replace("'", '')
					if policyType == "keyword": pItem.append(policyValue)
					else: print("Ignored unknow polocy: " + policyType)
				pGroup.append(pItem)
				policies.append(pGroup)	
			except: print("Error processing rules: " + str(element))
		else: print("Ignored unknow element: " + elementType)
	elif elementType == "server" or elementType == "route":
		try:
			if elementType == "server": servers.append([element[1].split(" ")[0],element[1].split(" ")[1] + " " + element[1].split(" ")[2]])
			elif elementType == "route": routers.append([element[1].split(" ")[0],element[1].split(" ")[1]])
			else: print("Ignored unknow element: " + elementType)
		except: print("Error processing server/router: " + str(element))
				
	else:
		print("Ignored unknow element: " + elementType)

print("servers="+str(servers))
print("routers="+str(routers))
print("policies="+str(policies))

print("""
function get(obj, key) {
        var target;
        obj.forEach(
                function(entry) {
                        if(entry[0] == key) target=entry[1];
                }
        )
        return target;
}

function FindProxyForURL(url, host) {
        host = host.toLowerCase()
        match = false;
        proxy = "DIRECT";
        policies.forEach(
                function(policy) {
                        policy_name = policy[0];
                        policy[1].forEach(
                                function(host_match) {
                                        if(host.includes(host_match)) match = true;
                                }
                        )
                        if(match) {
                                proxy = get(servers, get(routers, policy_name));
				match = false;
                        }
                }
        )
        return proxy;
}
""")
