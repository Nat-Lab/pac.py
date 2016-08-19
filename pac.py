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
					elif policyType == "cidr": pItem.append("cidr:"+policyValue)
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
var expandIPv6, ipaddr, ipv4Part, ipv4Regexes, ipv6Part, ipv6Regexes, matchCIDR, root;

ipaddr = {};

root = this;

matchCIDR = function(first, second, partSize, cidrBits) {
    var part, shift;
    if (first.length !== second.length) {
        throw new Error("ipaddr: cannot match CIDR for objects with different lengths");
    }
    part = 0;
    while (cidrBits > 0) {
        shift = partSize - cidrBits;
        if (shift < 0) {
            shift = 0;
        }
        if (first[part] >> shift !== second[part] >> shift) {
            return false;
        }
        cidrBits -= partSize;
        part += 1;
    }
    return true;
};

ipaddr.subnetMatch = function(address, rangeList, defaultName) {
    var j, len, rangeName, rangeSubnets, subnet;
    if (defaultName == null) {
        defaultName = 'unicast';
    }
    for (rangeName in rangeList) {
        rangeSubnets = rangeList[rangeName];
        if (rangeSubnets[0] && !(rangeSubnets[0] instanceof Array)) {
            rangeSubnets = [rangeSubnets];
        }
        for (j = 0, len = rangeSubnets.length; j < len; j++) {
            subnet = rangeSubnets[j];
            if (address.match.apply(address, subnet)) {
                return rangeName;
            }
        }
    }
    return defaultName;
};

ipaddr.IPv4 = (function() {
    function IPv4(octets) {
        var j, len, octet;
        if (octets.length !== 4) {
            throw new Error("ipaddr: ipv4 octet count should be 4");
        }
        for (j = 0, len = octets.length; j < len; j++) {
            octet = octets[j];
            if (!((0 <= octet && octet <= 255))) {
                throw new Error("ipaddr: ipv4 octet should fit in 8 bits");
            }
        }
        this.octets = octets;
    }

    IPv4.prototype.kind = function() {
        return 'ipv4';
    };

    IPv4.prototype.toString = function() {
        return this.octets.join(".");
    };

    IPv4.prototype.toByteArray = function() {
        return this.octets.slice(0);
    };

    IPv4.prototype.match = function(other, cidrRange) {
        var ref;
        if (cidrRange === void 0) {
            ref = other, other = ref[0], cidrRange = ref[1];
        }
        if (other.kind() !== 'ipv4') {
            throw new Error("ipaddr: cannot match ipv4 address with non-ipv4 one");
        }
        return matchCIDR(this.octets, other.octets, 8, cidrRange);
    };

    IPv4.prototype.SpecialRanges = {
        unspecified: [
            [new IPv4([0, 0, 0, 0]), 8]
        ],
        broadcast: [
            [new IPv4([255, 255, 255, 255]), 32]
        ],
        multicast: [
            [new IPv4([224, 0, 0, 0]), 4]
        ],
        linkLocal: [
            [new IPv4([169, 254, 0, 0]), 16]
        ],
        loopback: [
            [new IPv4([127, 0, 0, 0]), 8]
        ],
        "private": [
            [new IPv4([10, 0, 0, 0]), 8],
            [new IPv4([172, 16, 0, 0]), 12],
            [new IPv4([192, 168, 0, 0]), 16]
        ],
        reserved: [
            [new IPv4([192, 0, 0, 0]), 24],
            [new IPv4([192, 0, 2, 0]), 24],
            [new IPv4([192, 88, 99, 0]), 24],
            [new IPv4([198, 51, 100, 0]), 24],
            [new IPv4([203, 0, 113, 0]), 24],
            [new IPv4([240, 0, 0, 0]), 4]
        ]
    };

    IPv4.prototype.range = function() {
        return ipaddr.subnetMatch(this, this.SpecialRanges);
    };

    IPv4.prototype.toIPv4MappedAddress = function() {
        return ipaddr.IPv6.parse("::ffff:" + (this.toString()));
    };

    IPv4.prototype.prefixLengthFromSubnetMask = function() {
        var cidr, i, j, octet, stop, zeros, zerotable;
        zerotable = {
            0: 8,
            128: 7,
            192: 6,
            224: 5,
            240: 4,
            248: 3,
            252: 2,
            254: 1,
            255: 0
        };
        cidr = 0;
        stop = false;
        for (i = j = 3; j >= 0; i = j += -1) {
            octet = this.octets[i];
            if (octet in zerotable) {
                zeros = zerotable[octet];
                if (stop && zeros !== 0) {
                    return null;
                }
                if (zeros !== 8) {
                    stop = true;
                }
                cidr += zeros;
            } else {
                return null;
            }
        }
        return 32 - cidr;
    };

    return IPv4;

})();

ipv4Part = "(0?\\\d+|0x[a-f0-9]+)";

ipv4Regexes = {
    fourOctet: new RegExp("^" + ipv4Part + "\\\." + ipv4Part + "\\\." + ipv4Part + "\\\." + ipv4Part + "$", 'i'),
    longValue: new RegExp("^" + ipv4Part + "$", 'i')
};

ipaddr.IPv4.parser = function(string) {
    var match, parseIntAuto, part, shift, value;
    parseIntAuto = function(string) {
        if (string[0] === "0" && string[1] !== "x") {
            return parseInt(string, 8);
        } else {
            return parseInt(string);
        }
    };
    if (match = string.match(ipv4Regexes.fourOctet)) {
        return (function() {
            var j, len, ref, results;
            ref = match.slice(1, 6);
            results = [];
            for (j = 0, len = ref.length; j < len; j++) {
                part = ref[j];
                results.push(parseIntAuto(part));
            }
            return results;
        })();
    } else if (match = string.match(ipv4Regexes.longValue)) {
        value = parseIntAuto(match[1]);
        if (value > 0xffffffff || value < 0) {
            throw new Error("ipaddr: address outside defined range");
        }
        return ((function() {
            var j, results;
            results = [];
            for (shift = j = 0; j <= 24; shift = j += 8) {
                results.push((value >> shift) & 0xff);
            }
            return results;
        })()).reverse();
    } else {
        return null;
    }
};

ipaddr.IPv6 = (function() {
    function IPv6(parts) {
        var i, j, k, len, part, ref;
        if (parts.length === 16) {
            this.parts = [];
            for (i = j = 0; j <= 14; i = j += 2) {
                this.parts.push((parts[i] << 8) | parts[i + 1]);
            }
        } else if (parts.length === 8) {
            this.parts = parts;
        } else {
            throw new Error("ipaddr: ipv6 part count should be 8 or 16");
        }
        ref = this.parts;
        for (k = 0, len = ref.length; k < len; k++) {
            part = ref[k];
            if (!((0 <= part && part <= 0xffff))) {
                throw new Error("ipaddr: ipv6 part should fit in 16 bits");
            }
        }
    }

    IPv6.prototype.kind = function() {
        return 'ipv6';
    };

    IPv6.prototype.toString = function() {
        var compactStringParts, j, len, part, pushPart, state, stringParts;
        stringParts = (function() {
            var j, len, ref, results;
            ref = this.parts;
            results = [];
            for (j = 0, len = ref.length; j < len; j++) {
                part = ref[j];
                results.push(part.toString(16));
            }
            return results;
        }).call(this);
        compactStringParts = [];
        pushPart = function(part) {
            return compactStringParts.push(part);
        };
        state = 0;
        for (j = 0, len = stringParts.length; j < len; j++) {
            part = stringParts[j];
            switch (state) {
                case 0:
                    if (part === '0') {
                        pushPart('');
                    } else {
                        pushPart(part);
                    }
                    state = 1;
                    break;
                case 1:
                    if (part === '0') {
                        state = 2;
                    } else {
                        pushPart(part);
                    }
                    break;
                case 2:
                    if (part !== '0') {
                        pushPart('');
                        pushPart(part);
                        state = 3;
                    }
                    break;
                case 3:
                    pushPart(part);
            }
        }
        if (state === 2) {
            pushPart('');
            pushPart('');
        }
        return compactStringParts.join(":");
    };

    IPv6.prototype.toByteArray = function() {
        var bytes, j, len, part, ref;
        bytes = [];
        ref = this.parts;
        for (j = 0, len = ref.length; j < len; j++) {
            part = ref[j];
            bytes.push(part >> 8);
            bytes.push(part & 0xff);
        }
        return bytes;
    };

    IPv6.prototype.toNormalizedString = function() {
        var part;
        return ((function() {
            var j, len, ref, results;
            ref = this.parts;
            results = [];
            for (j = 0, len = ref.length; j < len; j++) {
                part = ref[j];
                results.push(part.toString(16));
            }
            return results;
        }).call(this)).join(":");
    };

    IPv6.prototype.match = function(other, cidrRange) {
        var ref;
        if (cidrRange === void 0) {
            ref = other, other = ref[0], cidrRange = ref[1];
        }
        if (other.kind() !== 'ipv6') {
            throw new Error("ipaddr: cannot match ipv6 address with non-ipv6 one");
        }
        return matchCIDR(this.parts, other.parts, 16, cidrRange);
    };

    IPv6.prototype.SpecialRanges = {
        unspecified: [new IPv6([0, 0, 0, 0, 0, 0, 0, 0]), 128],
        linkLocal: [new IPv6([0xfe80, 0, 0, 0, 0, 0, 0, 0]), 10],
        multicast: [new IPv6([0xff00, 0, 0, 0, 0, 0, 0, 0]), 8],
        loopback: [new IPv6([0, 0, 0, 0, 0, 0, 0, 1]), 128],
        uniqueLocal: [new IPv6([0xfc00, 0, 0, 0, 0, 0, 0, 0]), 7],
        ipv4Mapped: [new IPv6([0, 0, 0, 0, 0, 0xffff, 0, 0]), 96],
        rfc6145: [new IPv6([0, 0, 0, 0, 0xffff, 0, 0, 0]), 96],
        rfc6052: [new IPv6([0x64, 0xff9b, 0, 0, 0, 0, 0, 0]), 96],
        '6to4': [new IPv6([0x2002, 0, 0, 0, 0, 0, 0, 0]), 16],
        teredo: [new IPv6([0x2001, 0, 0, 0, 0, 0, 0, 0]), 32],
        reserved: [
            [new IPv6([0x2001, 0xdb8, 0, 0, 0, 0, 0, 0]), 32]
        ]
    };

    IPv6.prototype.range = function() {
        return ipaddr.subnetMatch(this, this.SpecialRanges);
    };

    IPv6.prototype.isIPv4MappedAddress = function() {
        return this.range() === 'ipv4Mapped';
    };

    IPv6.prototype.toIPv4Address = function() {
        var high, low, ref;
        if (!this.isIPv4MappedAddress()) {
            throw new Error("ipaddr: trying to convert a generic ipv6 address to ipv4");
        }
        ref = this.parts.slice(-2), high = ref[0], low = ref[1];
        return new ipaddr.IPv4([high >> 8, high & 0xff, low >> 8, low & 0xff]);
    };

    return IPv6;

})();

ipv6Part = "(?:[0-9a-f]+::?)+";

ipv6Regexes = {
    "native": new RegExp("^(::)?(" + ipv6Part + ")?([0-9a-f]+)?(::)?$", 'i'),
    transitional: new RegExp(("^((?:" + ipv6Part + ")|(?:::)(?:" + ipv6Part + ")?)") + (ipv4Part + "\\\." + ipv4Part + "\\\." + ipv4Part + "\\\." + ipv4Part + "$"), 'i')
};

expandIPv6 = function(string, parts) {
    var colonCount, lastColon, part, replacement, replacementCount;
    if (string.indexOf('::') !== string.lastIndexOf('::')) {
        return null;
    }
    colonCount = 0;
    lastColon = -1;
    while ((lastColon = string.indexOf(':', lastColon + 1)) >= 0) {
        colonCount++;
    }
    if (string.substr(0, 2) === '::') {
        colonCount--;
    }
    if (string.substr(-2, 2) === '::') {
        colonCount--;
    }
    if (colonCount > parts) {
        return null;
    }
    replacementCount = parts - colonCount;
    replacement = ':';
    while (replacementCount--) {
        replacement += '0:';
    }
    string = string.replace('::', replacement);
    if (string[0] === ':') {
        string = string.slice(1);
    }
    if (string[string.length - 1] === ':') {
        string = string.slice(0, -1);
    }
    return (function() {
        var j, len, ref, results;
        ref = string.split(":");
        results = [];
        for (j = 0, len = ref.length; j < len; j++) {
            part = ref[j];
            results.push(parseInt(part, 16));
        }
        return results;
    })();
};

ipaddr.IPv6.parser = function(string) {
    var j, len, match, octet, octets, parts;
    if (string.match(ipv6Regexes['native'])) {
        return expandIPv6(string, 8);
    } else if (match = string.match(ipv6Regexes['transitional'])) {
        parts = expandIPv6(match[1].slice(0, -1), 6);
        if (parts) {
            octets = [parseInt(match[2]), parseInt(match[3]), parseInt(match[4]), parseInt(match[5])];
            for (j = 0, len = octets.length; j < len; j++) {
                octet = octets[j];
                if (!((0 <= octet && octet <= 255))) {
                    return null;
                }
            }
            parts.push(octets[0] << 8 | octets[1]);
            parts.push(octets[2] << 8 | octets[3]);
            return parts;
        }
    }
    return null;
};

ipaddr.IPv4.isIPv4 = ipaddr.IPv6.isIPv6 = function(string) {
    return this.parser(string) !== null;
};

ipaddr.IPv4.isValid = function(string) {
    var e, error;
    try {
        new this(this.parser(string));
        return true;
    } catch (error) {
        e = error;
        return false;
    }
};

ipaddr.IPv4.isValidFourPartDecimal = function(string) {
    if (ipaddr.IPv4.isValid(string) && string.match(/^\d+(\.\d+){3}$/)) {
        return true;
    } else {
        return false;
    }
};

ipaddr.IPv6.isValid = function(string) {
    var e, error;
    if (typeof string === "string" && string.indexOf(":") === -1) {
        return false;
    }
    try {
        new this(this.parser(string));
        return true;
    } catch (error) {
        e = error;
        return false;
    }
};

ipaddr.IPv4.parse = ipaddr.IPv6.parse = function(string) {
    var parts;
    parts = this.parser(string);
    if (parts === null) {
        throw new Error("ipaddr: string is not formatted like ip address");
    }
    return new this(parts);
};

ipaddr.IPv4.parseCIDR = function(string) {
    var maskLength, match;
    if (match = string.match(/^(.+)\/(\d+)$/)) {
        maskLength = parseInt(match[2]);
        if (maskLength >= 0 && maskLength <= 32) {
            return [this.parse(match[1]), maskLength];
        }
    }
    throw new Error("ipaddr: string is not formatted like an IPv4 CIDR range");
};

ipaddr.IPv6.parseCIDR = function(string) {
    var maskLength, match;
    if (match = string.match(/^(.+)\/(\d+)$/)) {
        maskLength = parseInt(match[2]);
        if (maskLength >= 0 && maskLength <= 128) {
            return [this.parse(match[1]), maskLength];
        }
    }
    throw new Error("ipaddr: string is not formatted like an IPv6 CIDR range");
};

ipaddr.isValid = function(string) {
    return ipaddr.IPv6.isValid(string) || ipaddr.IPv4.isValid(string);
};

ipaddr.parse = function(string) {
    if (ipaddr.IPv6.isValid(string)) {
        return ipaddr.IPv6.parse(string);
    } else if (ipaddr.IPv4.isValid(string)) {
        return ipaddr.IPv4.parse(string);
    } else {
        throw new Error("ipaddr: the address has neither IPv6 nor IPv4 format");
    }
};

ipaddr.parseCIDR = function(string) {
    var e, error, error1;
    try {
        return ipaddr.IPv6.parseCIDR(string);
    } catch (error) {
        e = error;
        try {
            return ipaddr.IPv4.parseCIDR(string);
        } catch (error1) {
            e = error1;
            throw new Error("ipaddr: the address has neither IPv6 nor IPv4 CIDR format");
        }
    }
};

ipaddr.fromByteArray = function(bytes) {
    var length;
    length = bytes.length;
    if (length === 4) {
        return new ipaddr.IPv4(bytes);
    } else if (length === 16) {
        return new ipaddr.IPv6(bytes);
    } else {
        throw new Error("ipaddr: the binary input is neither an IPv6 nor IPv4 address");
    }
};

ipaddr.process = function(string) {
    var addr;
    addr = this.parse(string);
    if (addr.kind() === 'ipv6' && addr.isIPv4MappedAddress()) {
        return addr.toIPv4Address();
    } else {
        return addr;
    }
};


function get(obj, key) {
    var target;
    obj.forEach(
        function(entry) {
            if (entry[0] == key) target = entry[1];
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
                    if (shExpMatch(host_match, "cidr:*")) {
                        addr = ipaddr.parse(dnsResolve(host));
                        cidr = ipaddr.parseCIDR(host_match.split(":")[1])
                        if (addr.match(cidr)) match = true;
                    } else {
                        if (shExpMatch(host, "*" + host_match + "*")) match = true;
                    }
                }
            )
            if (match) {
                proxy = get(servers, get(routers, policy_name));
                match = false;
            }
        }
    )
    if (myVar === undefined) return "DIRECT;";
    return proxy + "; DIRECT;" || "DIRECT;";
}
""")
