package executor

import (
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	aty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/accountmanager/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/common"
)

/*
 * 实现交易的链上执行接口
 * 关键数据上链（statedb）并生成交易回执（log）
 */

// Exec_Register ...
func (a *Accountmanager) Exec_Register(payload *aty.Register, tx *types.Transaction, index int) (*types.Receipt, error) {
	action := NewAction(a, tx, index)
	return action.Register(payload)
}

// Exec_ResetKey ...
func (a *Accountmanager) Exec_ResetKey(payload *aty.ResetKey, tx *types.Transaction, index int) (*types.Receipt, error) {
	payload.Addr = common.FmtEthAddressWithFork(payload.Addr, a.GetAPI().GetConfig(), a.GetHeight())
	action := NewAction(a, tx, index)
	return action.Reset(payload)
}

// Exec_Transfer ...
func (a *Accountmanager) Exec_Transfer(payload *aty.Transfer, tx *types.Transaction, index int) (*types.Receipt, error) {
	action := NewAction(a, tx, index)
	return action.Transfer(payload)
}

// Exec_Supervise ...
func (a *Accountmanager) Exec_Supervise(payload *aty.Supervise, tx *types.Transaction, index int) (*types.Receipt, error) {
	action := NewAction(a, tx, index)
	return action.Supervise(payload)
}

// Exec_Apply ...
func (a *Accountmanager) Exec_Apply(payload *aty.Apply, tx *types.Transaction, index int) (*types.Receipt, error) {
	action := NewAction(a, tx, index)
	return action.Apply(payload)
}
