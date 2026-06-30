package omnilink

import (
	"errors"
	"fmt"

	omnilinkCommon "code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/secp256k1"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	wcom "code.corp.bcollie.net/omnilink/omnilink-base/wallet/common"
	x2ethTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	btcec_secp256k1 "github.com/btcsuite/btcd/btcec"
	"github.com/ethereum/go-ethereum/crypto"
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

func (omnilinkRelayer *Relayer4Omnilink) ImportPrivateKey(passphrase, privateKeyStr string) error {
	var driver secp256k1.Driver
	privateKeySli, err := omnilinkCommon.FromHex(privateKeyStr)
	if nil != err {
		return err
	}
	priKey, err := driver.PrivKeyFromBytes(privateKeySli)
	if nil != err {
		return err
	}

	omnilinkRelayer.rwLock.Lock()
	omnilinkRelayer.privateKey4Omnilink = priKey
	temp, _ := btcec_secp256k1.PrivKeyFromBytes(btcec_secp256k1.S256(), priKey.Bytes())
	omnilinkRelayer.privateKey4Omnilink_ecdsa = temp.ToECDSA()
	omnilinkRelayer.rwLock.Unlock()
	omnilinkRelayer.unlockChan <- start
	addr := address.PubKeyToAddr(address.DefaultID, priKey.PubKey().Bytes())

	encryptered := wcom.CBCEncrypterPrivkey([]byte(passphrase), privateKeySli)
	account := &x2ethTypes.Account4Relayer{
		Privkey: encryptered,
		Addr:    addr,
	}
	encodedInfo := omnilinkTypes.Encode(account)
	return omnilinkRelayer.db.SetSync(omnilinkAccountKey, encodedInfo)
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
func (omnilinkRelayer *Relayer4Omnilink) RestorePrivateKeys(passPhase string) (err error) {
	accountInfo, err := omnilinkRelayer.db.Get(omnilinkAccountKey)
	if nil == err {
		OmnilinkAccount := &x2ethTypes.Account4Relayer{}
		if err := omnilinkTypes.Decode(accountInfo, OmnilinkAccount); nil == err {
			decryptered := wcom.CBCDecrypterPrivkey([]byte(passPhase), OmnilinkAccount.Privkey)
			var driver secp256k1.Driver
			priKey, err := driver.PrivKeyFromBytes(decryptered)
			if nil != err {
				errInfo := fmt.Sprintf("Failed to PrivKeyFromBytes due to:%s", err.Error())
				relayerLog.Info("RestorePrivateKeys", "Failed to PrivKeyFromBytes:", err.Error())
				return errors.New(errInfo)
			}
			omnilinkRelayer.rwLock.Lock()
			omnilinkRelayer.privateKey4Omnilink = priKey
			omnilinkRelayer.privateKey4Omnilink_ecdsa, err = crypto.ToECDSA(priKey.Bytes())
			if nil != err {
				return err
			}
			omnilinkRelayer.rwLock.Unlock()
		}
	}

	omnilinkRelayer.rwLock.RLock()
	if nil != omnilinkRelayer.privateKey4Omnilink {
		omnilinkRelayer.unlockChan <- start
	}
	omnilinkRelayer.rwLock.RUnlock()

	return nil
}
