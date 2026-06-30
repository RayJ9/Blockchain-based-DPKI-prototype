package web3

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/client"
	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	rpcclient "code.corp.bcollie.net/omnilink/omnilink-base/rpc/client"
	ctypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/ethereum/go-ethereum/common/hexutil"
)

type web3Handler struct {
	cli rpcclient.ChannelClient
	cfg *ctypes.OmnilinkConfig
}

//NewWeb3API nwe web3 api object
func NewWeb3API(cfg *ctypes.OmnilinkConfig, c queue.Client, api client.QueueProtocolAPI) interface{} {
	w := &web3Handler{}
	w.cli.Init(c, api)
	w.cfg = cfg
	return w
}

//Sha3   web3_sha3
//Returns Keccak-256 (not the standardized SHA3-256) of the given data.
func (w *web3Handler) Sha3(input string) (string, error) {
	data, err := common.FromHex(input)
	if err != nil {
		return "", err
	}
	return hexutil.Encode(common.Sha3(data)), nil
}

//ClientVersion ...
//web3_clientVersion
func (w *web3Handler) ClientVersion() (string, error) {
	var subcfg struct {
		Web3CliVer string `json:"web3CliVer,omitempty"`
	}

	ctypes.MustDecode(w.cfg.GetSubConfig().RPC["eth"], &subcfg)
	return subcfg.Web3CliVer, nil
}
