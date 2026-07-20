package ethtxs

import (
	"fmt"
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/client/mocks"
	omnilinkCommon "code.corp.bcollie.net/omnilink/omnilink-base/common"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/secp256k1"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/testnode"
	ebrelayerTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

var (
	chainTestCfg = omnilinkTypes.NewOmnilinkConfig(omnilinkTypes.GetDefaultCfgstring())
)

func Test_RelayToOmnilink(t *testing.T) {
	var tx omnilinkTypes.Transaction
	var ret omnilinkTypes.Reply
	ret.IsOk = true

	mockapi := &mocks.QueueProtocolAPI{}
	// 这里对需要mock的方法打桩,Close是必须的，其它方法根据需要
	mockapi.On("Close").Return()
	mockapi.On("AddPushSubscribe", mock.Anything).Return(&ret, nil)
	mockapi.On("CreateTransaction", mock.Anything).Return(&tx, nil)
	mockapi.On("SendTx", mock.Anything).Return(&ret, nil)
	mockapi.On("SendTransaction", mock.Anything).Return(&ret, nil)
	mockapi.On("GetConfig", mock.Anything).Return(chainTestCfg, nil)

	mock33 := testnode.New("", mockapi)
	defer mock33.Close()
	rpcCfg := mock33.GetCfg().RPC
	// 这里必须设置监听端口，默认的是无效值
	rpcCfg.JrpcBindAddr = "127.0.0.1:8801"
	mock33.GetRPC().Listen()

	omnilinkPrivateKeyStr := "0xd627968e445f2a41c92173225791bae1ba42126ae96c32f28f97ff8f226e5c68"
	var driver secp256k1.Driver
	privateKeySli, err := omnilinkCommon.FromHex(omnilinkPrivateKeyStr)
	require.Nil(t, err)

	priKey, err := driver.PrivKeyFromBytes(privateKeySli)
	require.Nil(t, err)

	claim := &ebrelayerTypes.EthBridgeClaim{}

	fmt.Println("======================= testRelayLockToOmnilink =======================")
	_, err = RelayLockToOmnilink(priKey, claim, "http://127.0.0.1:8801")
	require.Nil(t, err)

	fmt.Println("======================= testRelayBurnToOmnilink =======================")
	_, err = RelayBurnToOmnilink(priKey, claim, "http://127.0.0.1:8801")
	require.Nil(t, err)
}
