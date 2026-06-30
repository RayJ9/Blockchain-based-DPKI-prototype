// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package system 系统基础插件包
package system

import (
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/address"        // init address driver
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/consensus/init" //register consensus init package
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/mempool/init"
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/p2p/init" // init p2p plugin
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system/store/init"
)
