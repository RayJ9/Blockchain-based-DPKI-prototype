// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package rpc

import (
	"context"

	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	vt "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
)

// IsSync query is sync
func (c *channelClient) IsSync(ctx context.Context, req *types.ReqNil) (*vt.PorsIsHealthy, error) {
	data, err := c.QueryConsensusFunc("pors", "IsHealthy", &types.ReqNil{})
	if err != nil {
		return nil, err
	}
	if resp, ok := data.(*vt.PorsIsHealthy); ok {
		return resp, nil
	}
	return nil, types.ErrDecode
}

// IsSync query is sync
func (c *Jrpc) IsSync(req *types.ReqNil, result *interface{}) error {
	data, err := c.cli.IsSync(context.Background(), req)
	if err != nil {
		return err
	}
	*result = data.IsHealthy
	return nil
}

// GetNodeInfo query node info
func (c *channelClient) GetNodeInfo(ctx context.Context, req *types.ReqNil) (*vt.PorsNodeInfoSet, error) {
	data, err := c.QueryConsensusFunc("pors", "NodeInfo", &types.ReqNil{})
	if err != nil {
		return nil, err
	}
	if resp, ok := data.(*vt.PorsNodeInfoSet); ok {
		return resp, nil
	}
	return nil, types.ErrDecode
}

// GetNodeInfo query node info
func (c *Jrpc) GetNodeInfo(req *types.ReqNil, result *interface{}) error {
	data, err := c.cli.GetNodeInfo(context.Background(), req)
	if err != nil {
		return err
	}
	*result = data
	return nil
}
