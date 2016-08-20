pac.py: A simple PAC Generator with nginx-style configuration
---

usage: `pac.py <configuration>`

There are four keywords: `server`, `rules`, `bypass`, and `route`, and seven rules keys `keywords`, `cidr`, `local_cidr`,`regexp`, `url_keyword`, `url_regexp` and `exact` available in configuration.

`server` are use to define a server, usage:

	server <server_name> <server_type> <host>:<port>;
	
`rules` are use to define a rules set, `keywords`, `cidr`, `regexp`, `url_keyword`, `url_regexp` and `exact` are use in the context of `rules`, usage:

	rules <rules_name> {
		... rules ...
	}

Here is some example of rules: 

	rules google {
		keyword "google"; # Matching domain contains 'google'.
		keyword "youtube";
		keyword "gstatic";
	}

	rules office {
		keyword "*.myofflice.local";
		cidr "10.0.1.0/24"; # Matching hosts in this CIDR.
	}
	
	rules action {
		regexp "*g*api*";
		url_keyword "font";
		url_regexp "*action.php?*&check=IP*";
	}
	
`bypass` are similar to `rules`, it is also a block containing rules. If any the rules there are matched, then no proxy will be used, see example:

	bypass {
		cidr "192.168.0.0/24";
		cidr "172.0.0.0/16";
		local_cidr "10.0.0.0/8"; # Match if *user* (yes, you.) in this CIDR. 
	}

`route` are use to assign a rules set to a server, usage:

	route <rules_name> <server_name>;
	
Here is a full example:

	server cn SOCKS5 127.0.0.1:1080;
	server us HTTPS us.my-server.com:8443;
	server jp HTTPS jp.my-server.com:8443;
	server office SOCKS5 tunnel.my-company.com:1080;

	rules music {
		keyword "163";
		keyword "xiami";
	}

	rules google {
		keyword "google";
		keyword "youtube";
	}

	rules dmm {
		keyword "dmm";
	}

	rules office {
		keyword "*.myofflice.local";
		cidr "172.0.88.0/24";
	}

	rules ipchecker {
		url_keyword "checkAddr.php";
		url_regexp "*action?key=*&do=myAddr*";
	}

	bypass {
		cidr "192.168.0.0/24";
		cidr "172.0.0.0/16";
	}

	route music cn;
	route dmm jp;
	route office office;
	route google us;
	route ipchecker cn;


used: whitequark/ipaddr.js (MIT License)

used: fatiherikli/nginxparser (MIT License)
	
(C) MagicNAT 2013
