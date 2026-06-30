package relayer

import (
	"errors"
	"fmt"
	"strconv"
	"sync"
	"sync/atomic"

	dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/relayer/ethereum"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/relayer/omnilink"
	relayerTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/utils"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/types"
	lru "github.com/hashicorp/golang-lru"
)

var (
	mlog = log15.New("relayer manager", "manager")
)

//status ...
const (
	Locked        = int32(1)
	Unlocked      = int32(99)
	EncryptEnable = int64(1)
)

//Manager ...
type Manager struct {
	omnilinkRelayer *omnilink.Relayer4Omnilink
	ethRelayer      *ethereum.Relayer4Ethereum
	store           *Store
	isLocked        int32
	mtx             sync.Mutex
	encryptFlag     int64
	passphase       string
	decimalLru      *lru.Cache
}

//NewRelayerManager ...
//1.验证人的私钥需要通过cli命令行进行导入，且omnilink和ethereum两种不同的验证人需要分别导入
//2.显示或者重新替换原有的私钥首先需要通过passpin进行unlock的操作
func NewRelayerManager(omnilinkRelayer *omnilink.Relayer4Omnilink, ethRelayer *ethereum.Relayer4Ethereum, db dbm.DB) *Manager {
	l, _ := lru.New(4096)
	manager := &Manager{
		omnilinkRelayer: omnilinkRelayer,
		ethRelayer:      ethRelayer,
		store:           NewStore(db),
		isLocked:        Locked,
		mtx:             sync.Mutex{},
		encryptFlag:     0,
		passphase:       "",
		decimalLru:      l,
	}
	manager.encryptFlag = manager.store.GetEncryptionFlag()
	return manager
}

//SetPassphase ...
func (manager *Manager) SetPassphase(setPasswdReq relayerTypes.ReqSetPasswd, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()

	// 第一次设置密码的时候才使用 后面用 ChangePasswd
	if EncryptEnable == manager.encryptFlag {
		return errors.New("passphase alreade exists")
	}

	// 密码合法性校验
	if !utils.IsValidPassWord(setPasswdReq.Passphase) {
		return omnilinkTypes.ErrInvalidPassWord
	}

	//使用密码生成passwdhash用于下次密码的验证
	newBatch := manager.store.NewBatch(true)
	err := manager.store.SetPasswordHash(setPasswdReq.Passphase, newBatch)
	if err != nil {
		mlog.Error("SetPassphase", "SetPasswordHash err", err)
		return err
	}
	//设置钱包加密标志位
	err = manager.store.SetEncryptionFlag(newBatch)
	if err != nil {
		mlog.Error("SetPassphase", "SetEncryptionFlag err", err)
		return err
	}

	err = newBatch.Write()
	if err != nil {
		mlog.Error("ProcWalletSetPasswd newBatch.Write", "err", err)
		return err
	}
	manager.passphase = setPasswdReq.Passphase
	atomic.StoreInt64(&manager.encryptFlag, EncryptEnable)

	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  "Succeed to set passphase",
	}
	return nil
}

//ChangePassphase ...
func (manager *Manager) ChangePassphase(setPasswdReq relayerTypes.ReqChangePasswd, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if setPasswdReq.OldPassphase == setPasswdReq.NewPassphase {
		return errors.New("the old password is the same as the new one")
	}
	// 新密码合法性校验
	if !utils.IsValidPassWord(setPasswdReq.NewPassphase) {
		return omnilinkTypes.ErrInvalidPassWord
	}
	//保存钱包的锁状态，需要暂时的解锁，函数退出时再恢复回去
	tempislock := atomic.LoadInt32(&manager.isLocked)
	atomic.CompareAndSwapInt32(&manager.isLocked, Locked, Unlocked)

	defer func() {
		//wallet.isWalletLocked = tempislock
		atomic.CompareAndSwapInt32(&manager.isLocked, Unlocked, tempislock)
	}()

	// 钱包已经加密需要验证oldpass的正确性
	if len(manager.passphase) == 0 && manager.encryptFlag == EncryptEnable {
		isok := manager.store.VerifyPasswordHash(setPasswdReq.OldPassphase)
		if !isok {
			mlog.Error("ChangePassphase Verify Oldpasswd fail!")
			return omnilinkTypes.ErrVerifyOldpasswdFail
		}
	}

	if len(manager.passphase) != 0 && setPasswdReq.OldPassphase != manager.passphase {
		mlog.Error("ChangePassphase Oldpass err!")
		return omnilinkTypes.ErrVerifyOldpasswdFail
	}

	//使用新的密码生成passwdhash用于下次密码的验证
	newBatch := manager.store.NewBatch(true)
	err := manager.store.SetPasswordHash(setPasswdReq.NewPassphase, newBatch)
	if err != nil {
		mlog.Error("ChangePassphase", "SetPasswordHash err", err)
		return err
	}
	//设置钱包加密标志位
	err = manager.store.SetEncryptionFlag(newBatch)
	if err != nil {
		mlog.Error("ChangePassphase", "SetEncryptionFlag err", err)
		return err
	}

	err = manager.ethRelayer.StoreAccountWithNewPassphase(setPasswdReq.NewPassphase, setPasswdReq.OldPassphase)
	if err != nil {
		mlog.Error("ChangePassphase", "StoreAccountWithNewPassphase err", err)
		return err
	}

	err = manager.omnilinkRelayer.StoreAccountWithNewPassphase(setPasswdReq.NewPassphase, setPasswdReq.OldPassphase)
	if err != nil {
		mlog.Error("ChangePassphase", "StoreAccountWithNewPassphase err", err)
		return err
	}

	err = newBatch.Write()
	if err != nil {
		mlog.Error("ProcWalletSetPasswd newBatch.Write", "err", err)
		return err
	}
	manager.passphase = setPasswdReq.NewPassphase
	atomic.StoreInt64(&manager.encryptFlag, EncryptEnable)

	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  "Succeed to change passphase",
	}
	return nil
}

//Unlock 进行unlok操作
func (manager *Manager) Unlock(passphase string, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if EncryptEnable != manager.encryptFlag {
		return errors.New("pls set passphase first")
	}
	if Unlocked == manager.isLocked {
		return errors.New("unlock already")
	}

	if !manager.store.VerifyPasswordHash(passphase) {
		return errors.New("wrong passphase")
	}

	if err := manager.omnilinkRelayer.RestorePrivateKeys(passphase); nil != err {
		info := fmt.Sprintf("Failed to RestorePrivateKeys for omnilinkRelayer due to:%s", err.Error())
		return errors.New(info)
	}
	if err := manager.ethRelayer.RestorePrivateKeys(passphase); nil != err {
		info := fmt.Sprintf("Failed to RestorePrivateKeys for ethRelayer due to:%s", err.Error())
		return errors.New(info)
	}

	manager.isLocked = Unlocked
	manager.passphase = passphase

	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  "Succeed to unlock",
	}

	return nil
}

//Lock 锁定操作，该操作一旦执行，就不能替换验证人的私钥，需要重新unlock之后才能修改
func (manager *Manager) Lock(param interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	manager.isLocked = Locked
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  "Succeed to lock",
	}
	return nil
}

//ImportOmnilinkRelayerPrivateKey 导入omnilinkrelayer验证人的私钥,该私钥实际用于向ethereum提交验证交易时签名使用
func (manager *Manager) ImportOmnilinkRelayerPrivateKey(importKeyReq relayerTypes.ImportKeyReq, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	privateKey := importKeyReq.PrivateKey
	if err := manager.checkPermission(); nil != err {
		return err
	}
	_, err := manager.omnilinkRelayer.ImportPrivateKey(manager.passphase, privateKey)
	if err != nil {
		mlog.Error("ImportOmnilinkValidatorPrivateKey", "Failed due to cause:", err.Error())
		return err
	}

	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  "Succeed to import private key for omnilink relayer",
	}
	return nil
}

//GenerateEthereumPrivateKey 生成以太坊私钥
func (manager *Manager) GenerateEthereumPrivateKey(param interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	account4Show := relayerTypes.Account4Show{}
	var err error
	account4Show.Privkey, account4Show.Addr, err = manager.ethRelayer.NewAccount(manager.passphase)
	if nil != err {
		return err
	}
	*result = account4Show
	return nil
}

//ImportOmnilinkPrivateKey4EthRelayer 为ethrelayer导入omnilink私钥，为向omnilink发送交易时进行签名使用
func (manager *Manager) ImportOmnilinkPrivateKey4EthRelayer(privateKey string, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	if err := manager.ethRelayer.ImportOmnilinkPrivateKey(manager.passphase, privateKey); nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  "Succeed to import omnilink private key for ethereum relayer",
	}
	return nil
}

//ShowOmnilinkRelayerValidator 显示在omnilink中以验证人validator身份进行登录的地址
func (manager *Manager) ShowOmnilinkRelayerValidator(param interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	var err error
	*result, err = manager.omnilinkRelayer.GetAccountAddr()
	if nil != err {
		return err
	}

	return nil
}

//ShowEthRelayerValidator 显示在Ethereum中以验证人validator身份进行登录的地址
func (manager *Manager) ShowEthRelayerValidator(param interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	var err error
	*result, err = manager.ethRelayer.GetValidatorAddr()
	if nil != err {
		return err
	}
	return nil
}

//IsValidatorActive ...
func (manager *Manager) IsValidatorActive(vallidatorAddr string, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	active, err := manager.ethRelayer.IsValidatorActive(vallidatorAddr)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: active,
		Msg:  "",
	}
	return nil
}

//ShowOperator ...
func (manager *Manager) ShowOperator(param interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	operator, err := manager.ethRelayer.ShowOperator()
	if nil != err {
		return err
	}
	*result = operator
	return nil
}

//DeployContrcts ...
func (manager *Manager) DeployContrcts(param interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	bridgeRegistry, err := manager.ethRelayer.DeployContrcts()
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  fmt.Sprintf("Contract BridgeRegistry's address is:%s", bridgeRegistry),
	}
	return nil
}

//CreateBridgeToken ...
func (manager *Manager) CreateBridgeToken(symbol string, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	tokenAddr, err := manager.ethRelayer.CreateBridgeToken(symbol)
	if nil != err {
		return err
	}
	*result = relayerTypes.ReplyAddr{
		IsOK: true,
		Addr: tokenAddr,
	}
	return nil
}

//CreateERC20Token ...
func (manager *Manager) CreateERC20Token(symbol string, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	tokenAddr, err := manager.ethRelayer.CreateERC20Token(symbol)
	if nil != err {
		return err
	}
	*result = relayerTypes.ReplyAddr{
		IsOK: true,
		Addr: tokenAddr,
	}
	return nil
}

//MintErc20 ...
func (manager *Manager) MintErc20(mintToken relayerTypes.MintToken, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	txhash, err := manager.ethRelayer.MintERC20Token(mintToken.TokenAddr, mintToken.Owner, mintToken.Amount)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//ApproveAllowance ...
func (manager *Manager) ApproveAllowance(approveAllowance relayerTypes.ApproveAllowance, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	txhash, err := manager.ethRelayer.ApproveAllowance(approveAllowance.OwnerKey, approveAllowance.TokenAddr, approveAllowance.Amount)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//Burn ...
func (manager *Manager) Burn(burn relayerTypes.Burn, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	txhash, err := manager.ethRelayer.Burn(burn.OwnerKey, burn.TokenAddr, burn.OmnilinkReceiver, burn.Amount)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//BurnAsync ...
func (manager *Manager) BurnAsync(burn relayerTypes.Burn, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	txhash, err := manager.ethRelayer.BurnAsync(burn.OwnerKey, burn.TokenAddr, burn.OmnilinkReceiver, burn.Amount)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//LockEthErc20AssetAsync ...
func (manager *Manager) LockEthErc20AssetAsync(lockEthErc20Asset relayerTypes.LockEthErc20, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	txhash, err := manager.ethRelayer.LockEthErc20AssetAsync(lockEthErc20Asset.OwnerKey, lockEthErc20Asset.TokenAddr, lockEthErc20Asset.Amount, lockEthErc20Asset.OmnilinkReceiver)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//LockEthErc20Asset ...
func (manager *Manager) LockEthErc20Asset(lockEthErc20Asset relayerTypes.LockEthErc20, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	if err := manager.checkPermission(); nil != err {
		return err
	}
	txhash, err := manager.ethRelayer.LockEthErc20Asset(lockEthErc20Asset.OwnerKey, lockEthErc20Asset.TokenAddr, lockEthErc20Asset.Amount, lockEthErc20Asset.OmnilinkReceiver)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//IsProphecyPending ...
func (manager *Manager) IsProphecyPending(claimID [32]byte, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	active, err := manager.ethRelayer.IsProphecyPending(claimID)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: active,
	}
	return nil
}

//GetBalance ...
func (manager *Manager) GetBalance(balanceAddr relayerTypes.BalanceAddr, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	balance, err := manager.ethRelayer.GetBalance(balanceAddr.TokenAddr, balanceAddr.Owner)
	if nil != err {
		return err
	}

	var d int64
	if balanceAddr.TokenAddr == "" || balanceAddr.TokenAddr == "0x0000000000000000000000000000000000000000" {
		d = 18
	} else {
		d, err = manager.GetDecimals(balanceAddr.TokenAddr)
		if err != nil {
			return errors.New("get decimals error")
		}
	}

	*result = relayerTypes.ReplyBalance{
		IsOK:    true,
		Balance: types.TrimZeroAndDot(strconv.FormatFloat(types.Toeth(balance, d), 'f', 4, 64)),
	}
	return nil
}

//ShowBridgeBankAddr ...
func (manager *Manager) ShowBridgeBankAddr(para interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	addr, err := manager.ethRelayer.ShowBridgeBankAddr()
	if nil != err {
		return err
	}
	*result = relayerTypes.ReplyAddr{
		IsOK: true,
		Addr: addr,
	}
	return nil
}

//ShowBridgeRegistryAddr ...
func (manager *Manager) ShowBridgeRegistryAddr(para interface{}, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	addr, err := manager.ethRelayer.ShowBridgeRegistryAddr()
	if nil != err {
		return err
	}
	*result = relayerTypes.ReplyAddr{
		IsOK: true,
		Addr: addr,
	}
	return nil
}

//ShowLockStatics ...
func (manager *Manager) ShowLockStatics(token relayerTypes.TokenStatics, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	balance, err := manager.ethRelayer.ShowLockStatics(token.TokenAddr)
	if nil != err {
		return err
	}
	var d int64
	if token.TokenAddr == "" || token.TokenAddr == "0x0000000000000000000000000000000000000000" {
		d = 18
	} else {
		d, err = manager.GetDecimals(token.TokenAddr)
		if err != nil {
			return errors.New("get decimals error")
		}
	}
	*result = relayerTypes.StaticsLock{
		Balance: strconv.FormatFloat(types.Toeth(balance, d), 'f', 4, 64),
	}
	return nil
}

//ShowDepositStatics ...
func (manager *Manager) ShowDepositStatics(token relayerTypes.TokenStatics, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	supply, err := manager.ethRelayer.ShowDepositStatics(token.TokenAddr)
	if nil != err {
		return err
	}
	var d int64
	if token.TokenAddr == "" || token.TokenAddr == "0x0000000000000000000000000000000000000000" {
		d = 18
	} else {
		d, err = manager.GetDecimals(token.TokenAddr)
		if err != nil {
			return errors.New("get decimals error")
		}
	}
	*result = relayerTypes.StaticsDeposit{
		Supply: strconv.FormatFloat(types.Toeth(supply, d), 'f', 4, 64),
	}
	return nil
}

//ShowTokenAddrBySymbol ...
func (manager *Manager) ShowTokenAddrBySymbol(token relayerTypes.TokenStatics, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	addr, err := manager.ethRelayer.ShowTokenAddrBySymbol(token.TokenAddr)
	if nil != err {
		return err
	}

	*result = relayerTypes.ReplyAddr{
		IsOK: true,
		Addr: addr,
	}
	return nil
}

//ShowTxReceipt ...
func (manager *Manager) ShowTxReceipt(txhash string, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	receipt, err := manager.ethRelayer.ShowTxReceipt(txhash)
	if nil != err {
		return err
	}
	*result = *receipt
	return nil
}

func (manager *Manager) checkPermission() error {
	if EncryptEnable != manager.encryptFlag {
		return errors.New("pls set passphase first")
	}
	if Locked == manager.isLocked {
		return errors.New("pls unlock this relay-manager first")
	}
	return nil
}

//ShowEthRelayer2EthTxs ...
func (manager *Manager) ShowEthRelayer2EthTxs(param interface{}, result *interface{}) error {
	*result = manager.ethRelayer.QueryTxhashRelay2Eth()
	return nil
}

//ShowEthRelayer2OmnilinkTxs ...
func (manager *Manager) ShowEthRelayer2OmnilinkTxs(param interface{}, result *interface{}) error {
	*result = manager.ethRelayer.QueryTxhashRelay2Omnilink()
	return nil
}

//ShowOmnilinkRelayer2EthTxs ...
func (manager *Manager) ShowOmnilinkRelayer2EthTxs(param interface{}, result *interface{}) error {
	*result = manager.omnilinkRelayer.QueryTxhashRelay2Eth()
	return nil
}

//ShowTxsEth2omnilinkTxLock ...
func (manager *Manager) ShowTxsEth2omnilinkTxLock(param interface{}, result *interface{}) error {
	return nil
}

//ShowTxsEth2omnilinkTxBurn ...
func (manager *Manager) ShowTxsEth2omnilinkTxBurn(param interface{}, result *interface{}) error {
	return nil
}

//ShowTxsOmnilinkToEthTxLock ...
func (manager *Manager) ShowTxsOmnilinkToEthTxLock(param interface{}, result *interface{}) error {

	return nil
}

//ShowTxsOmnilinkToEthTxBurn ...
func (manager *Manager) ShowTxsOmnilinkToEthTxBurn(param interface{}, result *interface{}) error {

	return nil
}

//TransferToken ...
func (manager *Manager) TransferToken(transfer relayerTypes.TransferToken, result *interface{}) error {
	manager.mtx.Lock()
	defer manager.mtx.Unlock()
	txhash, err := manager.ethRelayer.TransferToken(transfer.TokenAddr, transfer.FromKey, transfer.ToAddr, transfer.Amount)
	if nil != err {
		return err
	}
	*result = rpctypes.Reply{
		IsOk: true,
		Msg:  txhash,
	}
	return nil
}

//GetDecimals ...
func (manager *Manager) GetDecimals(tokenAddr string) (int64, error) {
	if d, ok := manager.decimalLru.Get(tokenAddr); ok {
		mlog.Info("GetDecimals", "from cache", d)
		return d.(int64), nil
	}

	if d, err := manager.store.Get(utils.CalAddr2DecimalsPrefix(tokenAddr)); err == nil {
		decimal, err := strconv.ParseInt(string(d), 10, 64)
		if err != nil {
			return 0, err
		}
		manager.decimalLru.Add(tokenAddr, decimal)
		mlog.Info("GetDecimals", "from DB", d)

		return decimal, nil
	}

	d, err := manager.ethRelayer.GetDecimals(tokenAddr)
	if err != nil {
		return 0, err
	}
	_ = manager.store.Set(utils.CalAddr2DecimalsPrefix(tokenAddr), []byte(strconv.FormatInt(int64(d), 10)))
	manager.decimalLru.Add(tokenAddr, int64(d))

	mlog.Info("GetDecimals", "from Node", d)

	return int64(d), nil
}
