// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package common

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

// FmtEthAddressWithFork 格式化eth十六进制地址格式, 包含fork检查
func FmtEthAddressWithFork(addr string, cfg *types.OmnilinkConfig, height int64) string {

	if address.IsEthAddress(addr) && cfg.IsFork(height, address.ForkEthAddressFormat) {
		return address.FormatEthAddress(addr)
	}
	return addr
}
