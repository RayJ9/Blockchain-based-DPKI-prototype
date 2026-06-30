package dht

import (
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/dht/protocol/broadcast" //register init package
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/dht/protocol/download"  //register init package
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/dht/protocol/p2pstore"  //register init package
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/dht/protocol/peer"      //register init package
)
