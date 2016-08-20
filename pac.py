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
					if policyType == "keyword": pItem.append("key:"+policyValue)
					elif policyType == "cidr": pItem.append("cidr:"+policyValue)
					elif policyType == "regexp": pItem.append("re:"+policyValue)
					elif policyType == "url_keyword": pItem.append("ukey:"+policyValue)
					elif policyType == "url_regexp": pItem.append("ure:"+policyValue)
					elif policyType == "exact": pItem.append("e:"+policyValue)
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
            if (entry[0] == key) target = entry[1];
        }
    )
    return target;
}

function getNetmask(bitCount) {
    var mask = [];
    for (i = 0; i < 4; i++) {
        var n = Math.min(bitCount, 8);
        mask.push(256 - Math.pow(2, 8 - n));
        bitCount -= n;
    }
    return mask.join('.');
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
                    policy_type = host_match.split(":")[0];
                    policy_term = host_match.split(":")[1];
                    switch (policy_type) {
                        case "key":
                            if (shExpMatch(host, "*" + policy_term + "*")) match = true;
                            break;
                        case "cidr":
                            subnet = policy_term.split("/")[0];
                            cidr = policy_term.split("/")[1];
                            netmask = getNetmask(cidr);
                            if (isInNet(host, subnet, netmask)) match = true;
                            break;
                        case "re":
                            if (shExpMatch(host, policy_term)) match = true;
                            break;
                        case "ukey":
                            if (shExpMatch(url, "*" + policy_term + "*")) match = true;
                            break;
                        case "ure":
                            if (shExpMatch(url, policy_term)) match = true;
                            break;
                        case "e":
                            if (shExpMatch(host, policy_term)) match = true;
                            break;
                    }
                }
            )
            if (match) {
                proxy = get(servers, get(routers, policy_name));
                match = false;
            }
        }
    )
    if (proxy === undefined) return "DIRECT;";
    return proxy + "; DIRECT;" || "DIRECT;";
}
""")
