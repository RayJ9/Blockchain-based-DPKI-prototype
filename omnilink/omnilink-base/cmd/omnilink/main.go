// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package main omnilink程序入口
package main

import (
	_ "code.corp.bcollie.net/omnilink/omnilink-base/system"
	"code.corp.bcollie.net/omnilink/omnilink-base/util/cli"
)

func main() {
	cli.RunOmnilink("", "")
}
