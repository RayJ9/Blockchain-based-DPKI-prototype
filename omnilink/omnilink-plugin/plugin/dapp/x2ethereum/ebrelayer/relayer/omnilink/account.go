package omnilink

import (
	omnilinkCommon "code.corp.bcollie.net/omnilink/omnilink-base/common"
	"github.com/ethereum/go-ethereum/crypto"

	//dbm "code.corp.bcollie.net/omnilink/omnilink-base/common/db"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	wcom "code.corp.bcollie.net/omnilink/omnilink-base/wallet/common"
	x2ethTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/x2ethereum/ebrelayer/types"
)

var (
	omnilinkAccountKey = []byte("OmnilinkAccount4Relayer")
	start              = int(1)
)

//GetAccount ...
func (omnilinkRelayer *Relayer4Omnilink) GetAccount(passphrase string) (privateKey, addr string, err error) {
	accountInfo, err := omnilinkRelayer.db.Get(omnilinkAccountKey)
	if nil != err {
		return "", "", err
	}
	ethAccount := &x2ethTypes.Account4Relayer{}
	if err := omnilinkTypes.Decode(accountInfo, ethAccount); nil != err {
		return "", "", err
	}
	decryptered := wcom.CBCDecrypterPrivkey([]byte(passphrase), ethAccount.Privkey)
	privateKey = omnilinkCommon.ToHex(decryptered)
	addr = ethAccount.Addr
	return
}

//GetAccountAddr ...
func (omnilinkRelayer *Relayer4Omnilink) GetAccountAddr() (addr string, err error) {
	accountInfo, err := omnilinkRelayer.db.Get(omnilinkAccountKey)
	if nil != err {
		relayerLog.Info("GetValidatorAddr", "Failed to get account from db due to:", err.Error())
		return "", err
	}
	ethAccount := &x2ethTypes.Account4Relayer{}
	if err := omnilinkTypes.Decode(accountInfo, ethAccount); nil != err {
		relayerLog.Info("GetValidatorAddr", "Failed to decode due to:", err.Error())
		return "", err
	}
	addr = ethAccount.Addr
	return
}

//ImportPrivateKey ...
func (omnilinkRelayer *Relayer4Omnilink) ImportPrivateKey(passphrase, privateKeyStr string) (addr string, err error) {
	privateKeySlice, err := omnilinkCommon.FromHex(privateKeyStr)
	if nil != err {
		return "", err
	}
	privateKey, err := crypto.ToECDSA(privateKeySlice)
	if nil != err {
		return "", err
	}

	ethSender := crypto.PubkeyToAddress(privateKey.PublicKey)
	omnilinkRelayer.privateKey4Ethereum = privateKey
	omnilinkRelayer.ethSender = ethSender
	omnilinkRelayer.unlock <- start

	addr = omnilinkCommon.ToHex(ethSender.Bytes())
	encryptered := wcom.CBCEncrypterPrivkey([]byte(passphrase), privateKeySlice)
	ethAccount := &x2ethTypes.Account4Relayer{
		Privkey: encryptered,
		Addr:    addr,
	}
	encodedInfo := omnilinkTypes.Encode(ethAccount)
	err = omnilinkRelayer.db.SetSync(omnilinkAccountKey, encodedInfo)

	return
}

//StoreAccountWithNewPassphase ...
func (omnilinkRelayer *Relayer4Omnilink) StoreAccountWithNewPassphase(newPassphrase, oldPassphrase string) error {
	accountInfo, err := omnilinkRelayer.db.Get(omnilinkAccountKey)
	if nil != err {
		relayerLog.Info("StoreAccountWithNewPassphase", "pls check account is created already, err", err)
		return err
	}
	ethAccount := &x2ethTypes.Account4Relayer{}
	if err := omnilinkTypes.Decode(accountInfo, ethAccount); nil != err {
		return err
	}
	decryptered := wcom.CBCDecrypterPrivkey([]byte(oldPassphrase), ethAccount.Privkey)
	encryptered := wcom.CBCEncrypterPrivkey([]byte(newPassphrase), decryptered)
	ethAccount.Privkey = encryptered
	encodedInfo := omnilinkTypes.Encode(ethAccount)
	return omnilinkRelayer.db.SetSync(omnilinkAccountKey, encodedInfo)
}

//RestorePrivateKeys ...
func (omnilinkRelayer *Relayer4Omnilink) RestorePrivateKeys(passphrase string) error {
	accountInfo, err := omnilinkRelayer.db.Get(omnilinkAccountKey)
	if nil != err {
		relayerLog.Info("No private key saved for Relayer4Omnilink")
		return nil
	}
	ethAccount := &x2ethTypes.Account4Relayer{}
	if err := omnilinkTypes.Decode(accountInfo, ethAccount); nil != err {
		relayerLog.Info("RestorePrivateKeys", "Failed to decode due to:", err.Error())
		return err
	}
	decryptered := wcom.CBCDecrypterPrivkey([]byte(passphrase), ethAccount.Privkey)
	privateKey, err := crypto.ToECDSA(decryptered)
	if nil != err {
		relayerLog.Info("RestorePrivateKeys", "Failed to ToECDSA:", err.Error())
		return err
	}

	omnilinkRelayer.rwLock.Lock()
	omnilinkRelayer.privateKey4Ethereum = privateKey
	omnilinkRelayer.ethSender = crypto.PubkeyToAddress(privateKey.PublicKey)
	omnilinkRelayer.rwLock.Unlock()
	omnilinkRelayer.unlock <- start
	return nil
}

//func (omnilinkRelayer *Relayer4Omnilink) UpdatePrivateKey(Passphrase, privateKey string) error {
//	return nil
//}
