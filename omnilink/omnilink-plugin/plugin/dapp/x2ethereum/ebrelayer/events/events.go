package events

import (
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
)

// Event : enum containing supported contract events
type Event int

var eventsLog = log.New("module", "ethereum_relayer")

const (
	// Unsupported : unsupported Omnilink or Ethereum event
	Unsupported Event = iota
	// MsgBurn : Omnilink event 'OmnilinkMsg' type MsgBurn
	MsgBurn
	// MsgLock :  Omnilink event 'OmnilinkMsg' type MsgLock
	MsgLock
	// LogLock : Ethereum event 'LockEvent'
	LogLock
	// LogOmnilinkTokenBurn : Ethereum event 'LogOmnilinkTokenBurn' in contract omnilinkBank
	LogOmnilinkTokenBurn
	// LogNewProphecyClaim : Ethereum event 'NewProphecyClaimEvent'
	LogNewProphecyClaim
)

//const
const (
	ClaimTypeBurn = uint8(1)
	ClaimTypeLock = uint8(2)
)

// String : returns the event type as a string
func (d Event) String() string {
	return [...]string{"unknown-x2ethereum", "OmnilinkToEthBurn", "OmnilinkToEthLock", "LogLock", "LogOmnilinkTokenBurn", "LogNewProphecyClaim"}[d]
}

// OmnilinkMsgAttributeKey : enum containing supported attribute keys
type OmnilinkMsgAttributeKey int

const (
	// UnsupportedAttributeKey : unsupported attribute key
	UnsupportedAttributeKey OmnilinkMsgAttributeKey = iota
	// OmnilinkSender : sender's address on Omnilink network
	OmnilinkSender
	// EthereumReceiver : receiver's address on Ethereum network
	EthereumReceiver
	// Coin : coin type
	Coin
	// TokenContractAddress : coin's corresponding contract address deployed on the Ethereum network
	TokenContractAddress
)

// String : returns the event type as a string
func (d OmnilinkMsgAttributeKey) String() string {
	return [...]string{"unsupported", "omnilink_sender", "ethereum_receiver", "amount", "token_contract_address"}[d]
}
