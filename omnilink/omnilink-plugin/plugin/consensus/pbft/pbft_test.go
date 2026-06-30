// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package pbft

import (
	"flag"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"testing"
	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/blockchain"
	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/limits"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/log"
	"code.corp.bcollie.net/omnilink/omnilink-base/executor"
	"code.corp.bcollie.net/omnilink/omnilink-base/p2p"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	"code.corp.bcollie.net/omnilink/omnilink-base/store"
	cty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/coins/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/wallet"

	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/store/init"
)

var (
	random       *rand.Rand
	transactions []*types.Transaction
	txSize       = 1000
)

func init() {
	err := limits.SetLimits()
	if err != nil {
		panic(err)
	}
	random = rand.New(rand.NewSource(types.Now().UnixNano()))
	log.SetLogLevel("info")
}
func TestPbft(t *testing.T) {
	q, chain, p2pnet, s, exec, cs, wallet := initEnvPbft()
	defer chain.Close()
	defer p2pnet.Close()
	defer exec.Close()
	defer s.Close()
	defer cs.Close()
	defer q.Close()
	defer wallet.Close()
	time.Sleep(5 * time.Second)

	sendReplyList(q)
	clearTestData()
}

func initEnvPbft() (queue.Queue, *blockchain.BlockChain, *p2p.Manager, queue.Module, *executor.Executor, queue.Module, queue.Module) {
	flag.Parse()
	omnilinkCfg := types.NewOmnilinkConfig(types.ReadFile("omnilink.test.toml"))
	var q = queue.New("channel")
	q.SetConfig(omnilinkCfg)
	cfg := omnilinkCfg.GetModuleConfig()
	cfg.Log.LogFile = ""
	sub := omnilinkCfg.GetSubConfig()

	chain := blockchain.New(omnilinkCfg)
	chain.SetQueueClient(q.Client())
	exec := executor.New(omnilinkCfg)
	exec.SetQueueClient(q.Client())
	omnilinkCfg.SetMinFee(0)
	s := store.New(omnilinkCfg)
	s.SetQueueClient(q.Client())
	cs := NewPbft(cfg.Consensus, sub.Consensus["pbft"])
	cs.SetQueueClient(q.Client())
	p2pnet := p2p.NewP2PMgr(omnilinkCfg)
	p2pnet.SetQueueClient(q.Client())
	walletm := wallet.New(omnilinkCfg)
	walletm.SetQueueClient(q.Client())

	return q, chain, p2pnet, s, exec, cs, walletm

}

func sendReplyList(q queue.Queue) {
	client := q.Client()
	client.Sub("mempool")
	var count int
	for msg := range client.Recv() {
		if msg.Ty == types.EventTxList {
			count++
			createReplyList(client.GetConfig(), "test"+strconv.Itoa(count))
			msg.Reply(client.NewMessage("consensus", types.EventReplyTxList,
				&types.ReplyTxList{Txs: transactions}))
			if count == 5 {
				time.Sleep(5 * time.Second)
				break
			}
		} else if msg.Ty == types.EventGetMempoolSize {
			msg.Reply(client.NewMessage("", 0, &types.MempoolSize{}))
		}
	}
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
	priv, err := cr.PrivKeyFromBytes(bkey)
	if err != nil {
		panic(err)
	}
	return priv
}

func createReplyList(cfg *types.OmnilinkConfig, account string) {

	var result []*types.Transaction
	for j := 0; j < txSize; j++ {
		//tx := &types.Transaction{}
		val := &cty.CoinsAction_Transfer{Transfer: &types.AssetsTransfer{Amount: 10}}
		action := &cty.CoinsAction{Value: val, Ty: cty.CoinsActionTransfer}
		tx := &types.Transaction{Execer: []byte(cfg.GetCoinExec()), Payload: types.Encode(action), Fee: 0}
		tx.To = "14qViLJfdGaP4EeHnDyJbEGQysnCpwn1gZ"

		tx.Nonce = random.Int63()
		tx.ChainID = cfg.GetChainID()

		tx.Sign(types.SECP256K1, getprivkey("CC38546E9E659D15E6B4893F0AB32A06D103931A8230B0BDE71459D2B27D6944"))
		result = append(result, tx)
	}
	//result = append(result, tx)
	transactions = result
}

func clearTestData() {
	err := os.RemoveAll("datadir")
	if err != nil {
		fmt.Println("delete datadir have a err:", err.Error())
	}
	err = os.RemoveAll("wallet")
	if err != nil {
		fmt.Println("delete wallet have a err:", err.Error())
	}
	fmt.Println("test data clear successfully!")
}
