package pow

import (
	"math/rand"
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/difficulty"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/consensus"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

func TestMineBlockMeetsTarget(t *testing.T) {
	cfg := types.NewOmnilinkConfig(types.GetDefaultCfgstring())
	client := &Client{
		BaseClient: drivers.NewBaseClient(&types.Consensus{Name: "pow"}),
		subcfg:     &subConfig{MaxNonceScan: 100000},
		rng:        rand.New(rand.NewSource(1)),
	}
	block := &types.Block{
		Height:     1,
		ParentHash: common.Sha256([]byte("parent")),
		TxHash:     common.Sha256([]byte("tx")),
		BlockTime:  1,
		Difficulty: 0x207fffff,
	}

	attempts, _, err := client.mineBlock(cfg, block)
	if err != nil {
		t.Fatalf("mineBlock failed: %v", err)
	}
	if attempts == 0 {
		t.Fatal("expected at least one hash attempt")
	}
	target := difficulty.CompactToBig(block.Difficulty)
	if hashToBig(block.Hash(cfg)).Cmp(target) > 0 {
		t.Fatalf("mined hash does not meet target")
	}
}

func TestNextMiningDelayUsesMaintainers(t *testing.T) {
	client := &Client{
		subcfg: &subConfig{MeanBlockMs: 300, Maintainers: 4, LocalMiners: 1, MinerID: 2},
		rng:    rand.New(rand.NewSource(1)),
	}
	delay, winner := client.nextMiningDelay()
	if delay < 0 {
		t.Fatalf("delay must be non-negative: %v", delay)
	}
	if winner != client.subcfg.MinerID {
		t.Fatalf("winner out of range: %d", winner)
	}
}
