package testnode

import (
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/util"

	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	_ "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin"
	pt "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/paracross/types"
	"github.com/stretchr/testify/assert"
)

func TestParaNode(t *testing.T) {
	para := NewParaNode(nil, nil)
	paraCfg := para.Para.GetAPI().GetConfig()
	defer para.Close()
	//通过rpc 发生信息
	tx := util.CreateTxWithExecer(paraCfg, para.Para.GetGenesisKey(), "user.p.test.none")
	assert.NotNil(t, tx)
	para.Para.SendTxRPC(tx)
	para.Para.WaitHeight(1)
	tx = util.CreateTxWithExecer(paraCfg, para.Para.GetGenesisKey(), "user.p.test.none")
	assert.NotNil(t, tx)
	para.Para.SendTxRPC(tx)
	para.Para.WaitHeight(2)

	res, err := para.Para.GetAPI().Query(pt.ParaX, "GetTitle", &types.ReqString{Data: "user.p.test."})
	assert.Nil(t, err)
	assert.Equal(t, int64(-1), res.(*pt.ParacrossStatus).Height)
}
