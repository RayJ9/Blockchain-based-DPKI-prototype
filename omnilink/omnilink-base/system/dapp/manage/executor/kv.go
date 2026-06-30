// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package executor

import (
	"fmt"

	mty "code.corp.bcollie.net/omnilink/omnilink-base/system/dapp/manage/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
)

func managerIDKey(id string) []byte {
	return []byte(fmt.Sprintf("%s-%s", types.ManagePrefix+mty.ManageX+"-id", id))
}
