package types

import (
	"math/big"

	etypes "github.com/ethereum/go-ethereum/core/types"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/common/hexutil"
)

// BlockDetailToEthBlock omnilink blockdetails transfer to  eth block format
func BlockDetailToEthBlock(details *types.BlockDetails, cfg *types.OmnilinkConfig, full bool) (*Block, error) {
	var block Block
	var header Header
	items := details.GetItems()
	if len(items) == 0 || items[0].GetBlock() == nil {
		return nil, types.ErrInvalidParam
	}
	fullblock := items[0]
	cblock := fullblock.GetBlock()
	header.Time = hexutil.Uint64(cblock.GetBlockTime())
	header.Number = (*hexutil.Big)(big.NewInt(cblock.Height))
	header.TxHash = common.BytesToHash(cblock.GetHeader(cfg).TxHash)
	header.Difficulty = (*hexutil.Big)(big.NewInt(int64(cblock.GetDifficulty())))
	header.ParentHash = common.BytesToHash(cblock.ParentHash)
	header.Root = common.BytesToHash(cblock.GetStateHash())
	blockTxs := cblock.GetTxs()
	if len(blockTxs) > 0 && blockTxs[0] != nil {
		header.Coinbase = common.HexToAddress(blockTxs[0].From())
	}
	//header.GasUsed=
	//暂不支持ReceiptHash,UncleHash
	//header.ReceiptHash=
	header.UncleHash = etypes.EmptyUncleHash

	//处理交易
	txs, fee, err := TxsToEthTxs(common.BytesToHash(cblock.Hash(cfg)), cblock.Height, blockTxs, cfg, full)
	if err != nil {
		return nil, err
	}
	if txs == nil {
		txs = []interface{}{}
	}
	header.GasUsed = hexutil.Uint64(fee)
	header.GasLimit = header.GasUsed
	block.Hash = common.BytesToHash(cblock.Hash(cfg)).Hex()

	block.Header = &header
	block.Uncles = []*Header{}
	block.Transactions = txs
	return &block, nil
}

// BlockHeaderToEthHeader transfer omnilink header to eth header
func BlockHeaderToEthHeader(cHeader *types.Header) (*Header, error) {
	var header Header
	header.Time = hexutil.Uint64(cHeader.GetBlockTime())
	header.Number = (*hexutil.Big)(big.NewInt(cHeader.Height))
	header.TxHash = common.BytesToHash(cHeader.TxHash)
	header.Difficulty = (*hexutil.Big)(big.NewInt(int64(cHeader.GetDifficulty())))
	header.ParentHash = common.BytesToHash(cHeader.ParentHash)
	header.Root = common.BytesToHash(cHeader.GetStateHash())
	return &header, nil
}
