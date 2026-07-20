package blockchain

import (
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

func TestCheckClockDrift(t *testing.T) {
	cfg := types.NewOmnilinkConfig(types.GetDefaultCfgstring())
	q := queue.New("channel")
	q.SetConfig(cfg)

	blockchain := &BlockChain{}
	blockchain.client = q.Client()
	blockchain.checkClockDrift()

	cfg.GetModuleConfig().NtpHosts = append(cfg.GetModuleConfig().NtpHosts, types.NtpHosts...)
	blockchain.checkClockDrift()
}
