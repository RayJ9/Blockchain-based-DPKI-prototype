// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import "code.corp.bcollie.net/omnilink/omnilink-base/types"

// Query_GetHashlocKById get hashlock instance
func (h *Hashlock) Query_GetHashlocKById(in []byte) (types.Message, error) {
	differTime := types.Now().UnixNano()/1e9 - h.GetBlockTime()
	clog.Error("Query action")
	return h.GetTxsByHashlockID(in, differTime)
}
