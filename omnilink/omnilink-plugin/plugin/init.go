package plugin

import (
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/consensus/init" //consensus init
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/crypto/init"    //crypto init
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/init"      //dapp init
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/mempool/init"   //mempool init
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/p2p/init"       //p2p init
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/store/init"     //store init
)
