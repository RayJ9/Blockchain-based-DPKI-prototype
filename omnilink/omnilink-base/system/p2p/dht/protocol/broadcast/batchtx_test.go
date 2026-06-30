package broadcast

import (
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/stretchr/testify/require"
)

func Test_batchTx(t *testing.T) {

	p, cancel := newTestProtocol()
	defer cancel()
	subChan := p.ps.Sub(psBroadcast)
	for i := 0; i < defaultMaxBatchTxNum+1; i++ {
		p.ps.Pub(&types.Transaction{}, psBatchTxTopic)
	}
	msg := <-subChan
	require.Equal(t, defaultMaxBatchTxNum, len(msg.(publishMsg).msg.(*types.Transactions).Txs))
	msg = <-subChan
	require.Equal(t, 1, len(msg.(publishMsg).msg.(*types.Transactions).Txs))
}
