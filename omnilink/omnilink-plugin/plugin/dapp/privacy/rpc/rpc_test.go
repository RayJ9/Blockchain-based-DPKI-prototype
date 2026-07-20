// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package rpc

import (
	"errors"
	"testing"

	"code.corp.bcollie.net/omnilink/omnilink-base/client"
	"code.corp.bcollie.net/omnilink/omnilink-base/client/mocks"
	rpctypes "code.corp.bcollie.net/omnilink/omnilink-base/rpc/types"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/privacy/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

func newGrpc(api client.QueueProtocolAPI) *channelClient {
	return &channelClient{
		ChannelClient: rpctypes.ChannelClient{QueueProtocolAPI: api},
	}
}

func newJrpc(api client.QueueProtocolAPI) *Jrpc {
	return &Jrpc{cli: newGrpc(api)}
}

func TestOmnilink_PrivacyTxList(t *testing.T) {
	api := new(mocks.QueueProtocolAPI)
	testOmnilink := newJrpc(api)
	actual := &pty.ReqPrivacyTransactionList{}
	api.On("ExecWalletFunc", "privacy", "PrivacyTransactionList", actual).Return(nil, errors.New("error value"))
	var testResult interface{}
	err := testOmnilink.GetPrivacyTxByAddr(actual, &testResult)
	t.Log(err)
	assert.Equal(t, nil, testResult)
	assert.NotNil(t, err)

	mock.AssertExpectationsForObjects(t, api)
}
