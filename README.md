pac.py: A simple PAC Generator with nginx-style configuration
---

usage: `pac.py <configuration>`

There are three keywords: `server`, `rules`, `keywords`, `cidr` and `route` available in configuration.

`server` are use to define a server, usage:

	server <server_name> <server_type> <host>:<port>;
	
`rules` are use to define a rules set, `keywords` and `cidr` are use in the context of `rules`, usage:

	rules <rules_name> {
		... rules ...
	}

Here is some example of rules: 

	rules google {
		keyword "google";
		keyword "youtube";
	}

	rules office {
		cidr "10.0.1.0/24";
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
		cidr "172.0.88.0/24";
	}

	route music cn;
	route dmm jp;
	route office office;
	route google us;
	
(C) MagicNAT 2013
