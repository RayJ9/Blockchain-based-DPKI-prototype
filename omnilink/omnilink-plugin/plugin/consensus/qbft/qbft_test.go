package qbft

import (
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/require"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	mty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/manage/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/util"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/testnode"
	vty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/qbftNode/types"
	"github.com/stretchr/testify/assert"

	//加载系统内置store, 不要依赖plugin
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/mempool/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/store/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/store/init"
)

var quitC chan struct{}

func init() {
	quitC = make(chan struct{}, 1)
}

// 执行： go test -cover
func TestQbft(t *testing.T) {
	mock33 := testnode.New("omnilink.qbft.toml", nil)
	cfg := mock33.GetClient().GetConfig()
	mock33.Listen()
	t.Log(mock33.GetGenesisAddress())
	go startNode(t)
	time.Sleep(3 * time.Second)

	configTx := configManagerTx()
	_, err := mock33.GetAPI().SendTx(configTx)
	require.Nil(t, err)
	mock33.WaitTx(configTx.Hash())

	addTx := addNodeTx()
	mock33.GetAPI().SendTx(addTx)
	mock33.WaitTx(addTx.Hash())

	txs := util.GenNoneTxs(cfg, mock33.GetGenesisKey(), 4)
	for i := 0; i < len(txs); i++ {
		mock33.GetAPI().SendTx(txs[i])
		mock33.WaitTx(txs[i].Hash())
	}

	testQuery(t, mock33)

	quitC <- struct{}{}
	mock33.Close()
	clearQbftData("datadir")
	time.Sleep(2 * time.Second)
}

func startNode(t *testing.T) {
	cfg2 := types.NewOmnilinkConfig(types.ReadFile("omnilink.qbft.toml"))
	sub := cfg2.GetSubConfig()
	qcfg, err := types.ModifySubConfig(sub.Consensus["qbft"], "privFile", "priv_validator_1.json")
	assert.Nil(t, err)
	qcfg, err = types.ModifySubConfig(qcfg, "dbPath", "datadir2/qbft")
	assert.Nil(t, err)
	qcfg, err = types.ModifySubConfig(qcfg, "port", 33002)
	assert.Nil(t, err)
	qcfg, err = types.ModifySubConfig(qcfg, "validatorNodes", []string{"127.0.0.1:33001"})
	assert.Nil(t, err)
	sub.Consensus["qbft"] = qcfg
	mock33_2 := testnode.NewWithConfig(cfg2, nil)
	mock33_2.Listen()
	time.Sleep(3 * time.Second)
	defer clearQbftData("datadir2")
	defer mock33_2.Close()

	for {
		select {
		case <-quitC:
			fmt.Println("node2 will stop")
			return
		default:
			txs := util.GenNoneTxs(cfg2, mock33_2.GetGenesisKey(), 1)
			mock33_2.GetAPI().SendTx(txs[0])
			time.Sleep(500 * time.Millisecond)
		}
	}
}

func addNodeTx() *types.Transaction {
	pubkey := "93E69B00BCBC817BE7E3370BA0228908C6F5E5458F781998CDD2FDF7A983EB18BCF57F838901026DC65EDAC9A1F3D251"
	nput := &vty.QbftNodeAction_Node{Node: &vty.QbftNode{PubKey: pubkey, Power: int64(5)}}
	action := &vty.QbftNodeAction{Value: nput, Ty: vty.QbftNodeActionUpdate}
	tx := &types.Transaction{Execer: []byte("qbftNode"), Payload: types.Encode(action), Fee: fee}
	tx.To = address.ExecAddress("qbftNode")
	tx.Sign(types.SECP256K1, getprivkey("CC38546E9E659D15E6B4893F0AB32A06D103931A8230B0BDE71459D2B27D6944"))
	return tx
}

func configManagerTx() *types.Transaction {
	v := &types.ModifyConfig{Key: "qbft-manager", Op: "add", Value: "14KEKbYtKKQm4wMthSK9J4La4nAiidGozt", Addr: ""}
	modify := &mty.ManageAction{
		Ty:    mty.ManageActionModifyConfig,
		Value: &mty.ManageAction_Modify{Modify: v},
	}
	tx := &types.Transaction{Execer: []byte("manage"), Payload: types.Encode(modify), Fee: fee}
	tx.To = address.ExecAddress("manage")
	tx.Sign(types.SECP256K1, getprivkey("CC38546E9E659D15E6B4893F0AB32A06D103931A8230B0BDE71459D2B27D6944"))
	return tx
}

func getprivkey(key string) crypto.PrivKey {
	cr, err := crypto.Load(types.GetSignName("", types.SECP256K1), -1)
	if err != nil {
		panic(err)
	}
	bkey, err := common.FromHex(key)
	if err != nil {
		panic(err)
	}
	priv, err := cr.PrivKeyFromBytes(bkey[:32])
	if err != nil {
		panic(err)
	}
	return priv
}

func testQuery(t *testing.T, mock *testnode.OmnilinkMock) {
	var flag bool
	err := mock.GetJSONC().Call("qbftNode.IsSync", &types.ReqNil{}, &flag)
	assert.Nil(t, err)
	assert.Equal(t, true, flag)

	var qstate vty.QbftState
	query := &rpctypes.Query4Jrpc{
		Execer:   vty.QbftNodeX,
		FuncName: "GetCurrentState",
	}
	err = mock.GetJSONC().Call("Omnilink.Query", query, &qstate)
	assert.Nil(t, err)
	assert.Len(t, qstate.Validators.Validators, 3)

	state := LoadState(&qstate)
	_, curVals := state.GetValidators()
	assert.Len(t, curVals.Validators, 3)
	assert.True(t, state.Equals(state.Copy()))

	var reply vty.QbftNodeInfoSet
	err = mock.GetJSONC().Call("qbftNode.GetNodeInfo", &types.ReqNil{}, &reply)
	assert.Nil(t, err)
	assert.Len(t, reply.Nodes, 3)
}

func clearQbftData(path string) {
	err := os.RemoveAll(path)
	if err != nil {
		fmt.Println("qbft data clear fail", err.Error())
	}
	fmt.Println("qbft data clear success")
}
