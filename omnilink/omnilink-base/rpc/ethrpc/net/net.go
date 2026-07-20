package net

import (
	"strconv"

	"code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/secp256k1eth"

	"code.corp.bcollie.net/omnilink/omnilink-base/client"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	rpcclient "code.corp.bcollie.net/omnilink/omnilink-base/rpc/client"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	ctypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/ethereum/go-ethereum/common/hexutil"
)

type netHandler struct {
	cli rpcclient.ChannelClient
	cfg *ctypes.OmnilinkConfig
}

//NewNetAPI create a net  api
func NewNetAPI(cfg *ctypes.OmnilinkConfig, c queue.Client, api client.QueueProtocolAPI) interface{} {
	p := &netHandler{}
	p.cli.Init(c, api)
	p.cfg = cfg
	return p
}

//PeerCount net_peerCount
func (n *netHandler) PeerCount() (string, error) {

	var in = types.P2PGetPeerReq{}
	reply, err := n.cli.PeerInfo(&in)
	if err != nil {
		return "0x0", err
	}

	numPeers := len(reply.Peers)
	return hexutil.EncodeUint64(uint64(numPeers)), nil
}

//Listening net_listening
func (n *netHandler) Listening() (bool, error) {
	return true, nil
}

//Version net_version
func (n *netHandler) Version() (string, error) {
	return strconv.FormatInt(secp256k1eth.GetEvmChainID(), 10), nil
}
