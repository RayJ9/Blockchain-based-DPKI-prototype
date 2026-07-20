// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package btcscript btc Script driver
package btcscript

import (
	"bytes"
	"errors"

	cryptocli "code.corp.bcollie.net/omnilink/omnilink-base/common/crypto/client"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/btcscript/script"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/secp256k1"
	nty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/none/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
)

//const
const (
	Name = "btcscript"
	ID   = 11
)

func init() {
	// 默认开启
	crypto.Register(Name, &Driver{}, crypto.WithRegOptionTypeID(ID))
}

//Driver 驱动, 除验证外，其余接口同secp256k1
type Driver struct {
	secp256k1.Driver
}

// Validate validate msg and signature
func (d Driver) Validate(msg, pk, sig []byte) error {
	ssig := &script.Signature{}
	err := types.Decode(sig, ssig)
	if err != nil {
		return errDecodeBtcSignature
	}

	//需要验证公钥和锁定脚本是否一一对应
	if !bytes.Equal(pk, common.Sha256(ssig.LockScript)) {
		return errInvalidLockScript
	}

	ctx := cryptocli.GetCryptoContext()
	// check btc script lock time , lockTime <= blockHeight
	if ssig.LockTime > ctx.CurrBlockTime {
		return errInvalidLockTime
	}

	// check btc script utxo sequence, delayBeginHeight+sequence <= blockHeight
	if ssig.UtxoSequence > 0 {

		tx := &types.Transaction{}
		err = types.Decode(msg, tx)
		if err != nil {
			return errDecodeValidateTx
		}
		reply, err := ctx.API.Query(nty.NoneX, nty.QueryGetDelayTxInfo, &types.ReqBytes{Data: tx.Hash()})
		delayInfo, ok := reply.(*nty.CommitDelayTxLog)
		if err != nil || !ok {
			return errQueryDelayBeginTime
		}
		// blocktime as delay time
		delayTime := ctx.CurrBlockTime - delayInfo.GetDelayBeginTimestamp()
		// block height as delay time
		if delayInfo.GetDelayBeginTimestamp() <= 0 {
			delayTime = ctx.CurrBlockHeight - delayInfo.GetDelayBeginHeight()
		}
		// ensure enough delay time
		if delayTime < ssig.UtxoSequence {
			return errInvalidUtxoSequence
		}
	}

	if err := script.CheckBtcScript(msg, ssig); err != nil {
		return errInvalidBtcSignature
	}

	return nil
}

var (
	errInvalidLockScript   = errors.New("errInvalidLockScript")
	errInvalidBtcSignature = errors.New("errInvalidBtcSignature")
	errDecodeBtcSignature  = errors.New("errDecodeBtcSignature")
	errDecodeValidateTx    = errors.New("errDecodeValidateTx")
	errInvalidLockTime     = errors.New("errInvalidLockTime")
	errQueryDelayBeginTime = errors.New("errQueryDelayBeginTime")
	errInvalidUtxoSequence = errors.New("errInvalidUtxoSequence")
)
