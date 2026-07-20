package types

//key
var (
	ProphecyKey                         = []byte("prefix_for_Prophecy")
	Eth2OmnilinkKey                     = []byte("prefix_for_Eth2Omnilink")
	WithdrawEthKey                      = []byte("prefix_for_WithdrawEth")
	OmnilinkToEthKey                    = []byte("prefix_for_OmnilinkToEth")
	WithdrawOmnilinkKey                 = []byte("prefix_for_WithdrawOmnilink")
	LastTotalPowerKey                   = []byte("prefix_for_LastTotalPower")
	ValidatorMapsKey                    = []byte("prefix_for_ValidatorMaps")
	ConsensusThresholdKey               = []byte("prefix_for_ConsensusThreshold")
	TokenSymbolTotalLockOrBurnAmountKey = []byte("prefix_for_TokenSymbolTotalLockOrBurnAmount-")
	TokenSymbolToTokenAddressKey        = []byte("prefix_for_TokenSymbolToTokenAddress-")
)

// log for x2ethereum
// log类型id值
const (
	TyUnknownLog = iota + 100
	TyEth2OmnilinkLog
	TyWithdrawEthLog
	TyWithdrawOmnilinkLog
	TyOmnilinkToEthLog
	TyAddValidatorLog
	TyRemoveValidatorLog
	TyModifyPowerLog
	TySetConsensusThresholdLog
	TyProphecyLog
	TyTransferLog
	TyTransferToExecLog
	TyWithdrawFromExecLog
)

// action类型id和name，这些常量可以自定义修改
const (
	TyUnknowAction = iota + 100
	TyEth2OmnilinkAction
	TyWithdrawEthAction
	TyWithdrawOmnilinkAction
	TyOmnilinkToEthAction
	TyAddValidatorAction
	TyRemoveValidatorAction
	TyModifyPowerAction
	TySetConsensusThresholdAction
	TyTransferAction
	TyTransferToExecAction
	TyWithdrawFromExecAction

	NameEth2OmnilinkAction          = "Eth2OmnilinkLock"
	NameWithdrawEthAction           = "Eth2OmnilinkBurn"
	NameWithdrawOmnilinkAction      = "OmnilinkToEthBurn"
	NameOmnilinkToEthAction         = "OmnilinkToEthLock"
	NameAddValidatorAction          = "AddValidator"
	NameRemoveValidatorAction       = "RemoveValidator"
	NameModifyPowerAction           = "ModifyPower"
	NameSetConsensusThresholdAction = "SetConsensusThreshold"
	NameTransferAction              = "Transfer"
	NameTransferToExecAction        = "TransferToExec"
	NameWithdrawFromExecAction      = "WithdrawFromExec"
)

//DefaultConsensusNeeded ...
const DefaultConsensusNeeded = int64(70)

//direct ...
const (
	DirEth2Omnilink  = "eth2omnilink"
	DirOmnilinkToEth = "omnilinktoeth"
	LockClaim        = "lock"
	BurnClaim        = "burn"
)

//DirectionType type
var DirectionType = [3]string{"", DirEth2Omnilink, DirOmnilinkToEth}

// query function name
const (
	FuncQueryEthProphecy               = "GetEthProphecy"
	FuncQueryValidators                = "GetValidators"
	FuncQueryTotalPower                = "GetTotalPower"
	FuncQueryConsensusThreshold        = "GetConsensusThreshold"
	FuncQuerySymbolTotalAmountByTxType = "GetSymbolTotalAmountByTxType"
	FuncQueryRelayerBalance            = "GetRelayerBalance"
)

//lock type
const (
	LockClaimType = int32(1)
	BurnClaimType = int32(2)
)
