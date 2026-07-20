// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"testing"

	apimock "code.corp.bcollie.net/omnilink/omnilink-base/client/mocks"
	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	dbmock "code.corp.bcollie.net/omnilink/omnilink-base/common/db/mocks"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/crypto/bls"
	pt "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/types"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/suite"
)

// 构造一个4个节点的平行链数据， 进行测试

type RewardTestSuite struct {
	suite.Suite
	stateDB dbm.KV
	localDB *dbmock.KVDB
	api     *apimock.QueueProtocolAPI

	exec   *Paracross
	action *action
}

func (suite *RewardTestSuite) SetupSuite() {

	suite.stateDB, _ = dbm.NewGoMemDB("state", "state", 1024)

	//suite.localDB, _ = dbm.NewGoMemDB("local", "local", 1024)
	suite.localDB = new(dbmock.KVDB)
	suite.api = new(apimock.QueueProtocolAPI)
	suite.api.On("GetConfig", mock.Anything).Return(omnilinkTestCfg, nil)

	suite.exec = newParacross().(*Paracross)
	suite.exec.SetAPI(suite.api)
	suite.exec.SetLocalDB(suite.localDB)
	suite.exec.SetStateDB(suite.stateDB)
	suite.exec.SetEnv(0, 0, 0)

	accountdb := suite.exec.GetCoinsAccount()
	suite.action = &action{coinsAccount: accountdb, db: suite.stateDB}

}

func TestRewardSuite(t *testing.T) {
	suite.Run(t, new(RewardTestSuite))
}

func (suite *RewardTestSuite) TestRewardBindAddr() {
	node := "1KSBd17H7ZK8iT37aJztFB22XGwsPTdwE4"
	addr := "1E5saiXVb9mW8wcWUUZjsHJPZs5GmdzuSY"
	key := calcParaBindMinerAddr(node, addr)
	newer := &pt.ParaBindMinerInfo{
		Addr:          addr,
		BindStatus:    opBind,
		BindCoins:     100,
		BlockTime:     100,
		BlockHeight:   1,
		ConsensusNode: node,
	}
	data := types.Encode(newer)
	suite.stateDB.Set(key, data)
	rst, err := suite.stateDB.Get(key)
	if err != nil {
		suite.T().Error("get setup title failed", err)
		return
	}
	var info pt.ParaBindMinerInfo
	types.Decode(rst, &info)
	suite.Equal(info.BindCoins, newer.BindCoins)

	addr2 := "1PUiGcbsccfxW3zuvHXZBJfznziph5miAo"
	new2 := *newer
	new2.Addr = addr2
	data = types.Encode(&new2)
	key = calcParaBindMinerAddr(node, addr2)
	suite.stateDB.Set(key, data)

	var list []*pt.ParaBindMinerInfo
	list = append(list, newer)
	list = append(list, &new2)

	recp, change, err := suite.action.rewardBindAddrList(50000005, node, list, 1)
	suite.Nil(err)
	suite.Equal(int64(5), change)
	suite.Equal(int32(types.ExecOk), recp.Ty)

}
