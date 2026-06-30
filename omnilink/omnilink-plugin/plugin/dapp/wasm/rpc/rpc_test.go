package rpc

import (
	"io/ioutil"
	"strings"
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/client/mocks"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	types2 "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/wasm/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

var cfg *types.OmnilinkConfig

func init() {
	cfg = types.NewOmnilinkConfig(strings.Replace(types.GetDefaultCfgstring(), "Title=\"local\"", "Title=\"omnilink\"", 1))
}

func TestJrpc_CheckContract(t *testing.T) {
	api := new(mocks.QueueProtocolAPI)
	api.On("Query", types2.WasmX, "Check", mock.Anything).Return(&types.Reply{}, nil)
	jrpc := &Jrpc{
		cli: &channelClient{
			rpctypes.ChannelClient{
				QueueProtocolAPI: api,
			},
		},
	}
	var result interface{}
	err := jrpc.CheckContract(&types2.QueryCheckContract{Name: "dice"}, &result)
	assert.Nil(t, err, "CheckContract error not nil")
	assert.Equal(t, false, result.(bool))
}

func TestJrpc_CreateContract(t *testing.T) {
	jrpc := &Jrpc{}
	code, err := ioutil.ReadFile("../contracts/dice/dice.wasm")
	assert.Nil(t, err, "read wasm file error")
	var result interface{}
	err = jrpc.CreateContract(&types2.WasmCreate{Name: "dice", Code: code}, &result)
	assert.Nil(t, err, "create contract error")
	t.Log(result)
}

func TestJrpc_CallContract(t *testing.T) {
	jrpc := &Jrpc{}
	var result interface{}
	err := jrpc.CallContract(&types2.WasmCall{Contract: "dice", Method: "play"}, &result)
	assert.Nil(t, err, "call contract error")
	t.Log(result)
}
