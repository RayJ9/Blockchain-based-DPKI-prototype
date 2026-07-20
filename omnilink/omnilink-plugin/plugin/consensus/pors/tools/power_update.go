package main

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"math/rand"
	"os"
	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/crypto"
	"code.corp.bcollie.net/omnilink/omnilink-base/system/crypto/secp256k1eth"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/crypto/bls"
	pty "code.corp.bcollie.net/omnilink/omnilink-plugin/plugin/dapp/pors/types"
	log "github.com/sirupsen/logrus"
	"google.golang.org/grpc"
)

var UserNames = []string{"A", "B", "C"}
var host = "127.0.0.1:8802"
var tstKe = "1A6F059D5D8BFB9B9AFEE2A9DADB7D6CCE29CEC2D7077F7A74A701356E53F64A" // for 0x49f90294233c864952cc90b3e00b25a3c3bc3ce9

var functionName = flag.String("function", "", "select function, create or send")
var autoHeight = flag.Bool("auto-height", false, "")
var height = flag.Int("height", 0, "chain height")
var ranAddr = flag.String("address", "", "")

func main() {
	log.Info("Power update")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [options]\n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()
	if functionName == nil {
		panic("function name nil")
	}

	switch *functionName {
	case "create":
		if checkUserKeyFileExists() != 0 {
			panic("Some files are already exists")
		}
		createUserKeys()
	case "send":
		if checkUserKeyFileExists() != len(UserNames) {
			panic("Key files lost")
		}
		if ranAddr == nil || len(*ranAddr) == 0 {
			panic("ran addr is empty")
		}
		sendTxToOmnilink(*autoHeight, *height, *ranAddr)
	default:
		flag.Usage()
		os.Exit(1)
	}
}

func getHeight(gcli types.OmnilinkClient) (int64, error) {
	header, err := gcli.GetLastHeader(context.Background(), &types.ReqNil{})
	if err != nil {
		log.Error("getHeight", "err", err)
		return 0, err
	}
	return header.Height, nil
}

func newGrpcConn(host string) *grpc.ClientConn {
	conn, err := grpc.Dial(host, grpc.WithInsecure())
	for err != nil {
		log.Error("grpc dial", "err", err)
		time.Sleep(time.Millisecond * 100)
		conn, err = grpc.Dial(host, grpc.WithInsecure())
	}
	return conn
}

func sendTxToOmnilink(autoHeight bool, height int, addr string) error {
	chainHeight := 0
	conn := newGrpcConn(host)
	defer conn.Close()

	gcli := types.NewOmnilinkClient(conn)

	if autoHeight {
		h, err := getHeight(gcli)
		if err != nil {
			log.Errorf("error getting height:%v", err)
		}
		chainHeight = int(h + 1)
	} else {
		if height == 0 {

		}
		chainHeight = height
	}

	tx, err := ConstructTransction(chainHeight, addr)
	if err != nil {
		log.Errorf("error creating transaction: %v", err)
		return err
	}
	_, err = gcli.SendTransaction(context.Background(), tx)
	if err != nil {
		log.Errorf("error sending transaction: %v", err)
		return err
	}

	return nil
}

func ConstructTransction(chainHeight int, addr string) (*types.Transaction, error) {
	proof, err := ConstructProof(chainHeight, addr)
	if err != nil {
		return nil, err
	}
	power := len(UserNames)

	value := &pty.PorsExecAction_PowerUpdate{
		PowerUpdate: &pty.PorsPowerUpdate{
			Address: addr,
			Power:   int64(power),
			Height:  int64(chainHeight),
			Proof:   proof,
		},
	}
	action := &pty.PorsExecAction{Value: value, Ty: pty.PorsActionPowerUpdate}
	tx := &types.Transaction{
		Payload: types.Encode(action),
		Nonce:   rand.Int63(),
		Execer:  []byte(pty.PorsX),
	}
	tx.To = address.ExecAddress(string(tx.Execer))

	dri := secp256k1eth.Driver{}
	tstKeyBytes, err := hex.DecodeString(tstKe)
	if err != nil {
		return nil, err
	}
	priv, err := dri.PrivKeyFromBytes(tstKeyBytes)
	if err != nil {
		return nil, err
	}

	tx.Sign(types.EncodeSignID(secp256k1eth.ID, types.EthAddressID), priv)
	return tx, nil
	//txHex := types.Encode(tx)
}

func ConstructProof(chainHeight int, address string) (*pty.PowerProof, error) {
	log.Infof("construct proof")
	// load from files
	message := fmt.Sprintf("%s:%d", address, chainHeight)
	dri := bls.Driver{}
	proof := pty.PowerProof{}
	sigs := []crypto.Signature{}
	for _, name := range UserNames {
		fileName := fmt.Sprintf("%s.txt", name)

		keyFileBytes, err := ioutil.ReadFile(fileName)
		if err != nil {
			panic(err)
		}

		keyFileS := KeyFitFile{}
		err = json.Unmarshal(keyFileBytes, &keyFileS)
		if err != nil {
			panic(err)
		}

		priKey, err := dri.PrivKeyFromBytes(keyFileS.PriKeyBytes)
		if err != nil {
			panic(err)
		}
		sig := priKey.Sign([]byte(message))
		sigs = append(sigs, sig)

		log.Infof("The key:%s, privKeyStr:%s, pubKeyStr:%s\n", keyFileS.KeyName, keyFileS.PriKeyStr, keyFileS.PubKeyStr)
		proof.PubkeyBytes = append(proof.PubkeyBytes, keyFileS.PubKeyBytes)
	}

	aggSig, err := dri.Aggregate(sigs)
	if err != nil {
		panic(err)
	}
	proof.AggregatedSig = aggSig.Bytes()

	return &proof, nil
}

type KeyFitFile struct {
	KeyName     string
	PriKeyBytes []byte
	PriKeyStr   string
	PubKeyBytes []byte
	PubKeyStr   string
}

func createUserKeys() {
	log.Infof("creating user keys")
	dri := bls.Driver{}

	for _, name := range UserNames {
		fileName := fmt.Sprintf("%s.txt", name)

		prikey, err := dri.GenKey()
		if err != nil {
			panic(err)
		}

		priKeyBytes := prikey.Bytes()

		priKeyBytesStr := hex.EncodeToString(priKeyBytes)

		pubKey := prikey.PubKey()
		pubKeyBytes := pubKey.Bytes()
		pubKeyBytesStr := hex.EncodeToString(pubKeyBytes)
		//pubKeyStr := pubKey.KeyString()

		keyFileS := KeyFitFile{
			KeyName:     name,
			PriKeyBytes: priKeyBytes,
			PriKeyStr:   priKeyBytesStr,
			PubKeyBytes: pubKeyBytes,
			PubKeyStr:   pubKeyBytesStr,
		}

		keyFileBytes, err := json.Marshal(&keyFileS)
		if err != nil {
			panic(err)
		}

		err = ioutil.WriteFile(fileName, keyFileBytes, 0644) // 0644 为文件权限
		if err != nil {
			log.Fatal(err)
		}
	}
	log.Infof("fininshed user keys")
}

func checkUserKeyFileExists() int {
	count := 0
	for _, name := range UserNames {
		fileName := fmt.Sprintf("%s.txt", name)
		if fileExists(fileName) {
			count++
		}
	}
	return count
}

func fileExists(filename string) bool {
	_, err := os.Stat(filename)
	return err == nil || !os.IsNotExist(err)
}
