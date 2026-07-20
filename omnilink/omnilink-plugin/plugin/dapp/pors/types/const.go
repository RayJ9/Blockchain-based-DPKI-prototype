// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package types

// PorsNodeX define
const PorsX = "pors"

// The power of node can't be updated in first sevevral blocks
const PorsNodeUpdateStartBlock = 4

// PorsNode action
const (
	PorsActionPowerUpdate = 1
	PorsActionBlockInfo   = 2
)

// action name
const (
	ActionPowerUpdate = "PowerUpdate"
	ActionBlockInfo   = "BlockInfo"
)
