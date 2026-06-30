package ethereum

import (
	"crypto/ecdsa"
	crand "crypto/rand"
	"crypto/sha256"
	"io"

	omnilinkCommon "code.corp.bcollie.net/omnilink/omnilink-base/common"
	omnilinkTypes "code.corp.bcollie.net/omnilink/omnilink-base/types"
	wcom "code.corp.bcollie.net/omnilink/omnilink-base/wallet/common"
	x2ethTypes "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/cross2eth/ebrelayer/types"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/common/math"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/pborman/uuid"
)

var (
	ethAccountKey = []byte("EthereumAccount4EthRelayer")
	start         = int(1)
)

//Key ...
type Key struct {
	ID uuid.UUID // Version 4 "random" for unique id not derived from key data
	// to simplify lookups we also store the address
	Address common.Address
	// we only store privkey as pubkey/address can be derived from it
	// privkey in this struct is always in plaintext
	PrivateKey *ecdsa.PrivateKey
}

//NewAccount ...
func NewAccount() (privateKeystr, addr string, err error) {
	_, privateKeystr, addr, err = newKeyAndStore(crand.Reader)
	if err != nil {
		return "", "", err
	}
	return
}

//GetAccount ...
func (ethRelayer *Relayer4Ethereum) GetAccount(passphrase string) (privateKey, addr string, err error) {
	accountInfo, err := ethRelayer.db.Get(ethAccountKey)
	if nil != err {
		return "", "", err
	}
	OmnilinkAccount := &x2ethTypes.Account4Relayer{}
	if err := omnilinkTypes.Decode(accountInfo, OmnilinkAccount); nil != err {
		return "", "", err
	}
	decryptered := wcom.CBCDecrypterPrivkey([]byte(passphrase), OmnilinkAccount.Privkey)
	privateKey = omnilinkCommon.ToHex(decryptered)
	addr = OmnilinkAccount.Addr
	return
}

//GetValidatorAddr ...
func (ethRelayer *Relayer4Ethereum) GetValidatorAddr() (validators x2ethTypes.ValidatorAddr4EthRelayer, err error) {
	var omnilinkAccountAddr string
	accountInfo, err := ethRelayer.db.Get(ethAccountKey)
	if nil == err {
		ethAccount := &x2ethTypes.Account4Relayer{}
		if err := omnilinkTypes.Decode(accountInfo, ethAccount); nil == err {
			omnilinkAccountAddr = ethAccount.Addr
		}
	}

	if 0 == len(omnilinkAccountAddr) {
		return x2ethTypes.ValidatorAddr4EthRelayer{}, x2ethTypes.ErrNoValidatorConfigured
	}

	validators = x2ethTypes.ValidatorAddr4EthRelayer{
		EthereumValidator: omnilinkAccountAddr,
	}
	return
}

func (ethRelayer *Relayer4Ethereum) ImportPrivateKey(passphrase, privateKeyStr string) (addr string, err error) {
	privateKeySlice, err := omnilinkCommon.FromHex(privateKeyStr)
	if nil != err {
		return "", err
	}
	privateKey, err := crypto.ToECDSA(privateKeySlice)
	if nil != err {
		return "", err
	}

	ethSender := crypto.PubkeyToAddress(privateKey.PublicKey)
	ethRelayer.privateKey4Ethereum = privateKey
	ethRelayer.ethSender = ethSender
	ethRelayer.unlockchan <- start

	addr = omnilinkCommon.ToHex(ethSender.Bytes())
	encryptered := wcom.CBCEncrypterPrivkey([]byte(passphrase), privateKeySlice)
	ethAccount := &x2ethTypes.Account4Relayer{
		Privkey: encryptered,
		Addr:    addr,
	}
	encodedInfo := omnilinkTypes.Encode(ethAccount)
	err = ethRelayer.db.SetSync(ethAccountKey, encodedInfo)

	return
}

//RestorePrivateKeys ...
func (ethRelayer *Relayer4Ethereum) RestorePrivateKeys(passphrase string) error {
	accountInfo, err := ethRelayer.db.Get(ethAccountKey)
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

	ethRelayer.rwLock.Lock()
	ethRelayer.privateKey4Ethereum = privateKey
	ethRelayer.ethSender = crypto.PubkeyToAddress(privateKey.PublicKey)
	ethRelayer.rwLock.Unlock()
	ethRelayer.unlockchan <- start
	return nil
}

//StoreAccountWithNewPassphase ...
func (ethRelayer *Relayer4Ethereum) StoreAccountWithNewPassphase(newPassphrase, oldPassphrase string) error {
	accountInfo, err := ethRelayer.db.Get(ethAccountKey)
	if nil != err {
		relayerLog.Info("StoreAccountWithNewPassphase", "pls check account is created already, err", err)
		return err
	}
	account := &x2ethTypes.Account4Relayer{}
	if err := omnilinkTypes.Decode(accountInfo, account); nil != err {
		return err
	}
	decryptered := wcom.CBCDecrypterPrivkey([]byte(oldPassphrase), account.Privkey)
	encryptered := wcom.CBCEncrypterPrivkey([]byte(newPassphrase), decryptered)
	account.Privkey = encryptered
	encodedInfo := omnilinkTypes.Encode(account)
	return ethRelayer.db.SetSync(ethAccountKey, encodedInfo)
}

//checksum: first four bytes of double-SHA256.
func checksum(input []byte) (cksum [4]byte) {
	h := sha256.New()
	_, err := h.Write(input)
	if err != nil {
		return
	}
	intermediateHash := h.Sum(nil)
	h.Reset()
	_, err = h.Write(intermediateHash)
	if err != nil {
		return
	}
	finalHash := h.Sum(nil)
	copy(cksum[:], finalHash[:])
	return
}

func newKeyAndStore(rand io.Reader) (privateKey *ecdsa.PrivateKey, privateKeyStr, addr string, err error) {
	key, err := newKey(rand)
	if err != nil {
		return nil, "", "", err
	}
	privateKey = key.PrivateKey
	privateKeyBytes := math.PaddedBigBytes(key.PrivateKey.D, 32)
	privateKeyStr = omnilinkCommon.ToHex(privateKeyBytes)
	addr = key.Address.Hex()
	return
}

func newKey(rand io.Reader) (*Key, error) {
	privateKeyECDSA, err := ecdsa.GenerateKey(crypto.S256(), rand)
	if err != nil {
		return nil, err
	}
	return newKeyFromECDSA(privateKeyECDSA), nil
}

func newKeyFromECDSA(privateKeyECDSA *ecdsa.PrivateKey) *Key {
	id := uuid.NewRandom()
	key := &Key{
		ID:         id,
		Address:    crypto.PubkeyToAddress(privateKeyECDSA.PublicKey),
		PrivateKey: privateKeyECDSA,
	}
	return key
}
