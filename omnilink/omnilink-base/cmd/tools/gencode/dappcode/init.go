// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package dappcode

import (
	_ "code.corp.bcollie.net/omnilink/omnilink-base/cmd/tools/gencode/dappcode/cmd"      //init cmd
	_ "code.corp.bcollie.net/omnilink/omnilink-base/cmd/tools/gencode/dappcode/commands" // init command
	_ "code.corp.bcollie.net/omnilink/omnilink-base/cmd/tools/gencode/dappcode/executor" // init executor
	_ "code.corp.bcollie.net/omnilink/omnilink-base/cmd/tools/gencode/dappcode/proto"    // init proto
	_ "code.corp.bcollie.net/omnilink/omnilink-base/cmd/tools/gencode/dappcode/rpc"      // init rpc
	_ "code.corp.bcollie.net/omnilink/omnilink-base/cmd/tools/gencode/dappcode/types"    // init types
)
