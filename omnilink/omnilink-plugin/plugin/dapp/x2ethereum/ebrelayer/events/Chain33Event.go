package events

import (
	"math/big"

	"github.com/ethereum/go-ethereum/common"
)

// OmnilinkMsg : contains data from MsgBurn and MsgLock events
type OmnilinkMsg struct {
	ClaimType            Event
	OmnilinkSender       []byte
	EthereumReceiver     common.Address
	TokenContractAddress common.Address
	Symbol               string
	Amount               *big.Int
}

// NewOmnilinkMsg : creates a new OmnilinkMsg
func NewOmnilinkMsg(
	claimType Event,
	omnilinkSender []byte,
	ethereumReceiver common.Address,
	symbol string,
	amount *big.Int,
	tokenContractAddress common.Address,
) OmnilinkMsg {
	// Package data into a OmnilinkMsg
	omnilinkMsg := OmnilinkMsg{
		ClaimType:            claimType,
		OmnilinkSender:       omnilinkSender,
		EthereumReceiver:     ethereumReceiver,
		Symbol:               symbol,
		Amount:               amount,
		TokenContractAddress: tokenContractAddress,
	}

	return omnilinkMsg
}
