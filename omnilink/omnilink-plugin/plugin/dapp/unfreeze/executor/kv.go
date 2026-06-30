// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"encoding/hex"
	"fmt"

	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/unfreeze/types"
)

var (
	idPrefix = "mavl-" + pty.UnfreezeX + "-"
)

func unfreezeID(txHash []byte) []byte {
	return []byte(fmt.Sprintf("%s%s", idPrefix, hex.EncodeToString(txHash)))
}

func unfreezeIDFromHex(txHash string) string {
	return fmt.Sprintf("%s%s", idPrefix, txHash)
}
