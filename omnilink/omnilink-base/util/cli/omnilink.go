// Copyright Fuzamei Corp. 2018 All Rights Reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// package cli RunOmnilink函数会加载各个模块，组合成区块链程序
//主循环由消息队列驱动。
//消息队列本身可插拔，可以支持各种队列
//同时共识模式也是可以插拔的。
//rpc 服务也是可以插拔的

package cli

import (
	"flag"
	"fmt"
	"net/http"
	_ "net/http/pprof" //
	"os"
	"path/filepath"
	"runtime"

	"code.corp.bcollie.net/omnilink/omnilink-base/common/address"

	cryptocli "code.corp.bcollie.net/omnilink/omnilink-base/common/crypto/client"

	"code.corp.bcollie.net/omnilink/omnilink-base/p2p"

	"code.corp.bcollie.net/omnilink/omnilink-base/metrics"

	"time"

	"code.corp.bcollie.net/omnilink/omnilink-base/blockchain"
	"code.corp.bcollie.net/omnilink/omnilink-base/util"

	"code.corp.bcollie.net/omnilink/omnilink-base/common"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/limits"
	clog "code.corp.bcollie.net/omnilink/omnilink-base/common/log"
	log "code.corp.bcollie.net/omnilink/omnilink-base/common/log/log15"
	"code.corp.bcollie.net/omnilink/omnilink-base/common/version"
	"code.corp.bcollie.net/omnilink/omnilink-base/consensus"
	"code.corp.bcollie.net/omnilink/omnilink-base/executor"
	"code.corp.bcollie.net/omnilink/omnilink-base/mempool"
	"code.corp.bcollie.net/omnilink/omnilink-base/queue"
	"code.corp.bcollie.net/omnilink/omnilink-base/rpc"
	"code.corp.bcollie.net/omnilink/omnilink-base/store"
	"code.corp.bcollie.net/omnilink/omnilink-base/types"
	"code.corp.bcollie.net/omnilink/omnilink-base/wallet"
	"google.golang.org/grpc/grpclog"
)

var (
	cpuNum      = runtime.NumCPU()
	configPath  = flag.String("f", "", "configfile")
	datadir     = flag.String("datadir", "", "data dir of omnilink, include logs and datas")
	versionCmd  = flag.Bool("v", false, "version")
	fixtime     = flag.Bool("fixtime", false, "fix time")
	waitPid     = flag.Bool("waitpid", false, "p2p stuck until seed save info wallet & wallet unlock")
	rollback    = flag.Int64("rollback", 0, "rollback block. WARNNING this command is only for test")
	save        = flag.Bool("save", false, "rollback save temporary block")
	importFile  = flag.String("import", "", "import block file name")
	exportTitle = flag.String("export", "", "export block title name")
	fileDir     = flag.String("filedir", "", "import/export block file dir,defalut current path")
	startHeight = flag.Int64("startheight", 0, "export block start height")
)

//RunOmnilink : run Omnilink
func RunOmnilink(name, defCfg string) {
	flag.Parse()
	if *versionCmd {
		fmt.Printf("%s %s\n", version.GetVersion(), version.BuildTime)
		return
	}
	if *configPath == "" {
		if name == "" {
			*configPath = "omnilink.toml"
		} else {
			*configPath = name + ".toml"
		}
	}
	d, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	log.Info("current dir:", "dir", d)
	err = os.Chdir(pwd())
	if err != nil {
		panic(err)
	}
	d, err = os.Getwd()
	if err != nil {
		panic(err)
	}
	log.Info("current dir:", "dir", d)
	err = limits.SetLimits()
	if err != nil {
		panic(err)
	}
	//set config: bityuan 用 bityuan.toml 这个配置文件
	omnilinkCfg := types.NewOmnilinkConfig(types.MergeCfg(types.ReadFile(*configPath), defCfg))
	cfg := omnilinkCfg.GetModuleConfig()
	if *datadir != "" {
		util.ResetDatadir(cfg, *datadir)
	}
	if *fixtime {
		cfg.FixTime = *fixtime
	}
	if *waitPid {
		cfg.P2P.WaitPid = *waitPid
	}

	if len(cfg.NtpHosts) <= 0 {
		cfg.NtpHosts = append(cfg.NtpHosts, types.NtpHosts...)
	}
	if cfg.FixTime {
		go fixtimeRoutine(cfg.NtpHosts)
	}
	//compare minFee in wallet, mempool, exec
	//set file log
	clog.SetFileLog(cfg.Log)
	//set grpc log
	f, err := createFile(cfg.P2P.GrpcLogFile)
	if err != nil {
		glogv2 := grpclog.NewLoggerV2(os.Stdout, os.Stdout, os.Stdout)
		grpclog.SetLoggerV2(glogv2)
	} else {
		glogv2 := grpclog.NewLoggerV2WithVerbosity(f, f, f, 10)
		grpclog.SetLoggerV2(glogv2)
	}
	//set watching
	t := time.Tick(10 * time.Second)
	go func() {
		for range t {
			watching()
		}
	}()
	//set pprof
	go func() {
		if cfg.Pprof != nil {
			err := http.ListenAndServe(cfg.Pprof.ListenAddr, nil)
			if err != nil {
				log.Info("ListenAndServe", "listen addr", cfg.Pprof.ListenAddr, "err", err)
			}
		} else {
			err := http.ListenAndServe("localhost:6060", nil)
			if err != nil {
				log.Info("ListenAndServe", "listen addr localhost:6060 err", err)
			}
		}
	}()
	//set maxprocs
	runtime.GOMAXPROCS(cpuNum)
	//开始区块链模块加载
	//channel, rabitmq 等
	version.SetLocalDBVersion(cfg.Store.LocalDBVersion)
	version.SetStoreDBVersion(cfg.Store.StoreDBVersion)
	version.SetAppVersion(cfg.Version)
	log.Info(cfg.Title + "-app:" + version.GetAppVersion() + " omnilink:" + version.GetVersion() + " localdb:" + version.GetLocalDBVersion() + " statedb:" + version.GetStoreDBVersion())
	log.Info("loading queue")
	q := queue.New("channel")
	q.SetConfig(omnilinkCfg)

	address.Init(cfg.Address)
	crypto := cryptocli.New()
	crypto.SetQueueClient(q.Client())
	log.Info("loading mempool module")
	mem := mempool.New(omnilinkCfg)
	mem.SetQueueClient(q.Client())

	log.Info("loading execs module")
	exec := executor.New(omnilinkCfg)
	exec.SetQueueClient(q.Client())

	log.Info("loading blockchain module")
	cfg.BlockChain.RollbackBlock = *rollback
	cfg.BlockChain.RollbackSave = *save
	chain := blockchain.New(omnilinkCfg)
	chain.SetQueueClient(q.Client())

	log.Info("loading store module")
	s := store.New(omnilinkCfg)
	s.SetQueueClient(q.Client())

	chain.Upgrade()

	log.Info("loading consensus module")
	cs := consensus.New(omnilinkCfg)
	cs.SetQueueClient(q.Client())

	//jsonrpc, grpc, channel 三种模式
	rpcapi := rpc.New(omnilinkCfg)
	rpcapi.SetQueueClient(q.Client())

	log.Info("loading wallet module")
	walletm := wallet.New(omnilinkCfg)
	walletm.SetQueueClient(q.Client())

	chain.Rollbackblock()
	//导入/导出区块通过title
	if *importFile != "" {
		chain.ImportBlockProc(*importFile, *fileDir)
	}
	if *exportTitle != "" {
		chain.ExportBlockProc(*exportTitle, *fileDir, *startHeight)
	}
	log.Info("loading p2p module")
	var network queue.Module
	if cfg.P2P.Enable {
		network = p2p.NewP2PMgr(omnilinkCfg)
	} else {
		network = &util.MockModule{Key: "p2p"}
	}
	network.SetQueueClient(q.Client())

	health := util.NewHealthCheckServer(q.Client())
	health.Start(cfg.Health)
	metrics.StartMetrics(omnilinkCfg)
	defer func() {
		//close all module,clean some resource
		log.Info("begin close health module")
		health.Close()
		log.Info("begin close blockchain module")
		chain.Close()
		log.Info("begin close crypto module")
		crypto.Close()
		log.Info("begin close mempool module")
		mem.Close()
		log.Info("begin close P2P module")
		network.Close()
		log.Info("begin close execs module")
		exec.Close()
		log.Info("begin close store module")
		s.Close()
		log.Info("begin close consensus module")
		cs.Close()
		log.Info("begin close rpc module")
		rpcapi.Close()
		log.Info("begin close wallet module")
		walletm.Close()
		log.Info("begin close queue module")
		q.Close()

	}()
	q.Start()
}

func createFile(filename string) (*os.File, error) {
	f, err := os.OpenFile(filename, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return nil, err
	}
	return f, nil
}

func watching() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	log.Info("GC runtime info:", "NumGoroutine:", runtime.NumGoroutine())
	log.Info("GC runtime info:", "Mem:", m.Sys/(1024*1024))
	log.Info("GC runtime info:", "HeapAlloc:", m.HeapAlloc/(1024*1024))
}

func pwd() string {
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		panic(err)
	}
	return dir
}

func fixtimeRoutine(hosts []string) {
	for i := 0; i < len(hosts); i++ {
		t, err := common.GetNtpTime(hosts[i])
		if err == nil {
			log.Info("time", "host", hosts[i], "now", t)
		} else {
			log.Error("time", "err", err)
		}
	}
	t := common.GetRealTimeRetry(hosts, 10)
	if !t.IsZero() {
		//update
		types.SetTimeDelta(int64(time.Until(t)))
		log.Info("change time", "delta", time.Until(t), "real.now", types.Now())
	}
	//时间请求频繁一点:
	ticket := time.NewTicker(time.Minute * 1)
	defer ticket.Stop()

	for range ticket.C {
		t = common.GetRealTimeRetry(hosts, 10)
		if !t.IsZero() {
			//update
			log.Info("change time", "delta", time.Until(t))
			types.SetTimeDelta(int64(time.Until(t)))
		}
	}
}
