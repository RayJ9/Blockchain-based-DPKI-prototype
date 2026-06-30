// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.
package types

import (
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	"github.com/stretchr/testify/require"
)

func TestAddressID(t *testing.T) {

	var cryptoID, addressID int32

	for ; cryptoID <= crypto.MaxManualTypeID; cryptoID++ {
		addressID = 0
		for ; addressID <= address.MaxID; addressID++ {
			signID := EncodeSignID(cryptoID, addressID)
			require.Equal(t, addressID, ExtractAddressID(signID))
			require.Equal(t, cryptoID, ExtractCryptoID(signID))
			dupSignID := EncodeSignID(signID, addressID)
			require.Equal(t, signID, dupSignID)
		}
	}
}
