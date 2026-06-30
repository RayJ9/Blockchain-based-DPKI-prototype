// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package pow implements a lightweight PoW consensus driver.
package pow

import (
	"bytes"
	"errors"
	"math"
	"math/big"
	"math/rand"
	"sync"
	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/difficulty"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/merkle"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	drivers "code.corp.bcollie.net/omnilink/omnilink-base/system/consensus"
	cty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/coins/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/util"
)

const (
	defaultMaintainers = int64(4)
	defaultMeanBlockMs = int64(300)
	idleSleep          = 100 * time.Millisecond
	hashCheckInterval  = uint64(4096)
)

var powlog = log.New("module", "pow")

// Client is a PoW consensus client.
type Client struct {
	*drivers.BaseClient
	subcfg *subConfig
	rng    *rand.Rand
	rngMu  sync.Mutex
}

type subConfig struct {
	Genesis          string `json:"genesis"`
	GenesisBlockTime int64  `json:"genesisBlockTime"`
	DifficultyBits   uint32 `json:"difficultyBits"`
	MeanBlockMs      int64  `json:"meanBlockMs"`
	Maintainers      int64  `json:"maintainers"`
	LocalMiners      int64  `json:"localMiners"`
	Miners           int64  `json:"miners"`
	MinerID          int64  `json:"minerId"`
	MineEmpty        bool   `json:"mineEmpty"`
	DisableMining    bool   `json:"disableMining"`
	BenchMode        bool   `json:"benchMode"`
	MaxNonceScan     uint64 `json:"maxNonceScan"`
	Seed             int64  `json:"seed"`
}

func init() {
	drivers.Reg("pow", New)
	drivers.QueryData.Register("pow", &Client{})
}

// New creates a PoW consensus client.
func New(cfg *types.Consensus, sub []byte) queue.Module {
	c := drivers.NewBaseClient(cfg)
	var subcfg subConfig
	if sub != nil {
		types.MustDecode(sub, &subcfg)
	}
	if subcfg.Genesis == "" {
		subcfg.Genesis = cfg.Genesis
	}
	if subcfg.GenesisBlockTime == 0 {
		subcfg.GenesisBlockTime = cfg.GenesisBlockTime
	}
	if subcfg.Maintainers == 0 {
		subcfg.Maintainers = subcfg.Miners
	}
	if subcfg.Maintainers <= 0 {
		subcfg.Maintainers = defaultMaintainers
	}
	if subcfg.LocalMiners <= 0 {
		subcfg.LocalMiners = 1
	}
	if subcfg.MeanBlockMs <= 0 {
		subcfg.MeanBlockMs = defaultMeanBlockMs
	}
	seed := subcfg.Seed
	if seed == 0 {
		seed = types.Now().UnixNano()
	}
	client := &Client{
		BaseClient: c,
		subcfg:     &subcfg,
		rng:        rand.New(rand.NewSource(seed)),
	}
	c.SetChild(client)
	return client
}

// Close closes the PoW consensus client.
func (client *Client) Close() {
	powlog.Info("consensus pow closed")
}

// GetGenesisBlockTime returns the genesis block time.
func (client *Client) GetGenesisBlockTime() int64 {
	return client.subcfg.GenesisBlockTime
}

// CreateGenesisTx creates the genesis transaction.
func (client *Client) CreateGenesisTx() (ret []*types.Transaction) {
	var tx types.Transaction
	cfg := client.GetAPI().GetConfig()
	tx.Execer = []byte(cfg.GetCoinExec())
	tx.To = client.subcfg.Genesis
	g := &cty.CoinsAction_Genesis{}
	g.Genesis = &types.AssetsGenesis{}
	g.Genesis.Amount = 1e8 * cfg.GetCoinPrecision()
	tx.Payload = types.Encode(&cty.CoinsAction{Value: g, Ty: cty.CoinsActionGenesis})
	ret = append(ret, &tx)
	return ret
}

// ProcEvent handles consensus events not handled by BaseClient.
func (client *Client) ProcEvent(msg *queue.Message) bool {
	return false
}

// CheckBlock verifies PoW difficulty and the mined header hash.
func (client *Client) CheckBlock(parent *types.Block, current *types.BlockDetail) error {
	if current == nil || current.Block == nil {
		return types.ErrInvalidParam
	}
	block := current.Block
	if len(block.Txs) == 0 && !client.subcfg.MineEmpty {
		return types.ErrEmptyTx
	}
	expected := client.difficultyBits(block.Height)
	if block.Difficulty != expected {
		return types.ErrBlockHeaderDifficulty
	}
	target := difficulty.CompactToBig(block.Difficulty)
	if target.Sign() <= 0 {
		return types.ErrBlockHeaderDifficulty
	}
	cfg := client.GetAPI().GetConfig()
	if hashToBig(block.Hash(cfg)).Cmp(target) > 0 {
		powlog.Error("CheckBlock pow target mismatch", "height", block.Height,
			"hash", common.ToHex(block.Hash(cfg)), "bits", block.Difficulty)
		return types.ErrBlockHeaderDifficulty
	}
	return nil
}

// CreateBlock mines PoW blocks. Each process samples its own exponential
// mining clock; running Maintainers processes gives the configured aggregate
// block-arrival mean.
func (client *Client) CreateBlock() {
	types.AssertConfig(client.GetAPI())
	cfg := client.GetAPI().GetConfig()
	for {
		if client.IsClosed() {
			powlog.Info("create block stop")
			return
		}
		if client.subcfg.DisableMining {
			time.Sleep(idleSleep)
			continue
		}
		if !client.IsMining() || !(client.IsCaughtUp() || client.Cfg.ForceMining) {
			time.Sleep(idleSleep)
			continue
		}

		delay, winner := client.nextMiningDelay()
		if client.sleepOrClosed(delay) {
			return
		}

		lastBlock := client.GetCurrentBlock()
		if lastBlock == nil {
			time.Sleep(idleSleep)
			continue
		}
		parentHash := lastBlock.Hash(cfg)
		// Bind transactions after the PoW clock fires so a non-empty block
		// drains the current mempool instead of mining an old empty snapshot.
		maxTxNum := int(cfg.GetP(lastBlock.Height + 1).MaxTxNumber)
		txs := client.RequestTx(maxTxNum, nil)
		txs = client.CheckTxDup(txs)
		if len(txs) == 0 || (client.subcfg.BenchMode && len(txs) < maxTxNum) {
			if !client.subcfg.MineEmpty {
				time.Sleep(idleSleep)
				continue
			}
		}

		var newblock types.Block
		newblock.ParentHash = parentHash
		newblock.Height = lastBlock.Height + 1
		client.AddTxsToBlock(&newblock, txs)
		if len(newblock.Txs) == 0 && !client.subcfg.MineEmpty {
			continue
		}
		if cfg.IsFork(newblock.Height, "ForkRootHash") {
			newblock.Txs = types.TransactionSort(newblock.Txs)
		}
		newblock.TxHash = merkle.CalcMerkleRoot(cfg, newblock.Height, newblock.Txs)
		newblock.Difficulty = client.difficultyBits(newblock.Height)
		newblock.BlockTime = types.Now().Unix()
		if lastBlock.BlockTime > newblock.BlockTime {
			newblock.BlockTime = lastBlock.BlockTime
		}

		preExecBeg := types.Now()
		if !client.preExecBlock(lastBlock, &newblock) {
			time.Sleep(idleSleep)
			continue
		}
		preExecCost := types.Since(preExecBeg)

		attempts, mineCost, err := client.mineBlock(cfg, &newblock)
		if err != nil {
			powlog.Error("PowMineBlock", "height", newblock.Height, "err", err, "attempts", attempts)
			time.Sleep(idleSleep)
			continue
		}

		current := client.GetCurrentBlock()
		if current == nil || !bytes.Equal(current.Hash(cfg), parentHash) {
			powlog.Info("PowStaleBlock", "height", newblock.Height)
			continue
		}

		writeBeg := types.Now()
		err = client.WriteBlock(lastBlock.StateHash, &newblock)
		writeCost := types.Since(writeBeg)
		if err != nil {
			powlog.Error("PowWriteBlock", "height", newblock.Height, "err", err)
			time.Sleep(idleSleep)
			continue
		}
		powlog.Info("PowNewBlock", "height", newblock.Height, "txs", len(newblock.Txs),
			"bits", newblock.Difficulty, "nonce", newblock.Version, "maintainer", winner,
			"minerId", client.subcfg.MinerID, "localMiners", client.subcfg.LocalMiners,
			"poissonDelay", delay, "preExec", preExecCost, "mine", mineCost,
			"attempts", attempts, "writeBlock", writeCost,
			"hash", common.ToHex(newblock.Hash(cfg)))
	}
}

// CmpBestBlock breaks equal-work ties by preferring the lower PoW hash.
func (client *Client) CmpBestBlock(newBlock *types.Block, cmpBlock *types.Block) bool {
	if newBlock == nil || cmpBlock == nil {
		return false
	}
	cfg := client.GetAPI().GetConfig()
	return hashToBig(newBlock.Hash(cfg)).Cmp(hashToBig(cmpBlock.Hash(cfg))) < 0
}

func (client *Client) difficultyBits(height int64) uint32 {
	if client.subcfg.DifficultyBits != 0 {
		return client.subcfg.DifficultyBits
	}
	return client.GetAPI().GetConfig().GetP(height).PowLimitBits
}

func (client *Client) preExecBlock(parent *types.Block, block *types.Block) bool {
	detail, deltx, err := util.PreExecBlock(client.GetQueueClient(), parent.StateHash, block, false, false, false)
	if err != nil {
		powlog.Error("PowPreExecBlock", "height", block.Height, "err", err)
		return false
	}
	if detail == nil || detail.Block == nil {
		powlog.Error("PowPreExecBlock", "height", block.Height, "err", types.ErrExecBlockNil)
		return false
	}
	if detail.Block != block {
		*block = *detail.Block
	}
	if len(deltx) > 0 {
		powlog.Info("PowPreExecBlockDelTx", "height", block.Height, "deltx", len(deltx))
	}
	return true
}

func (client *Client) mineBlock(cfg *types.OmnilinkConfig, block *types.Block) (uint64, time.Duration, error) {
	target := difficulty.CompactToBig(block.Difficulty)
	if target.Sign() <= 0 {
		return 0, 0, types.ErrBlockHeaderDifficulty
	}
	startNonce := client.nextNonce()
	beg := types.Now()
	for attempts := uint64(1); ; attempts++ {
		block.Version = int64(startNonce + attempts - 1)
		if hashToBig(block.Hash(cfg)).Cmp(target) <= 0 {
			return attempts, types.Since(beg), nil
		}
		if client.subcfg.MaxNonceScan > 0 && attempts >= client.subcfg.MaxNonceScan {
			return attempts, types.Since(beg), errors.New("pow max nonce scan exceeded")
		}
		if attempts%hashCheckInterval == 0 && client.IsClosed() {
			return attempts, types.Since(beg), queue.ErrIsQueueClosed
		}
	}
}

func (client *Client) nextNonce() uint64 {
	client.rngMu.Lock()
	defer client.rngMu.Unlock()
	return uint64(client.rng.Int63())
}

func (client *Client) nextMiningDelay() (time.Duration, int64) {
	if client.subcfg.MeanBlockMs <= 0 {
		return 0, 0
	}
	maintainers := client.subcfg.Maintainers
	if maintainers <= 0 {
		maintainers = 1
	}
	localMiners := client.subcfg.LocalMiners
	if localMiners <= 0 {
		localMiners = 1
	}
	perMaintainerMeanMs := float64(client.subcfg.MeanBlockMs) * float64(maintainers)
	best := math.MaxFloat64
	var winner int64

	client.rngMu.Lock()
	for i := int64(0); i < localMiners; i++ {
		sample := client.rng.ExpFloat64() * perMaintainerMeanMs
		if sample < best {
			best = sample
			winner = client.subcfg.MinerID + i
		}
	}
	client.rngMu.Unlock()

	return time.Duration(best * float64(time.Millisecond)), winner
}

func (client *Client) sleepOrClosed(delay time.Duration) bool {
	if delay <= 0 {
		return client.IsClosed()
	}
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-timer.C:
		return client.IsClosed()
	case <-client.Context.Done():
		return true
	}
}

func hashToBig(hash []byte) *big.Int {
	copyHash := make([]byte, len(hash))
	copy(copyHash, hash)
	return difficulty.HashToBig(copyHash)
}
