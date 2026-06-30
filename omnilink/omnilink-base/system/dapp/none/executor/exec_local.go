// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	nty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/none/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

// ExecLocal_CommitDelayTx exec local commit delay tx
func (n *None) ExecLocal_CommitDelayTx(commit *nty.CommitDelayTx, tx *types.Transaction, receipt *types.ReceiptData, index int) (*types.LocalDBSet, error) {
	return nil, nil
}
