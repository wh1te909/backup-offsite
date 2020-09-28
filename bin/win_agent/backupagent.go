//go:generate goversioninfo -icon=onit.ico -manifest=goversioninfo.exe.manifest -gofile=versioninfo.go

// to build:
// go generate
// go build -ldflags="-X 'main.endpoint=nats.example.com' -X 'main.token=REPLACE_WITH_TOKEN'"
// don't add .go file to build command or won't pickup the resource.syso
package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	ps "github.com/elastic/go-sysinfo"
	nats "github.com/nats-io/nats.go"
	"github.com/ugorji/go/codec"
)

var (
	debuglog *os.File
	logger   *log.Logger
	endpoint string
	token    string
	veeamExe = "Veeam.EndPoint.Manager.exe"
	version  = "1.3.0"
)

type proc struct {
	Name    string   `json:"name"`
	Pid     int      `json:"pid"`
	Ppid    int      `json:"ppid"`
	Cmdline []string `json:"cmdline"`
}

type procList []proc

type simpleRet struct {
	AgentID string `json:"id"`
	Ret     string `json:"ret"`
}

type backupRet struct {
	AgentID string   `json:"id"`
	Ret     string   `json:"ret"`
	Pid     int      `json:"pid"`
	Name    string   `json:"proc_name"`
	Cmdline []string `json:"cmdline"`
}

type infoRet struct {
	AgentID string   `json:"id"`
	Ret     string   `json:"ret"`
	Procs   procList `json:"procs"`
}

type pongRet struct {
	AgentID string `json:"id"`
	Ret     string `json:"ret"`
	Payload string `json:"msg"`
}

func main() {
	ver := flag.Bool("version", false, "Prints version")
	flag.Parse()

	if *ver {
		fmt.Println(fmt.Sprintf("Tactical Backup %s", version))
		return
	}

	setupLogging()
	defer debuglog.Close()

	logger.Println("Backup agent starting...")

	agentid := getAgentID()

	opts := []nats.Option{nats.Name("Tactical Backup Agent"), nats.Token(token)}
	opts = setupConnOptions(opts)

	server := fmt.Sprintf("nats://%s:4222", endpoint)
	nc, err := nats.Connect(server, opts...)
	if err != nil {
		logger.Println(err)
	}

	var data map[string]string
	var response []byte

	nc.Subscribe(agentid, func(msg *nats.Msg) {

		setupLogging()
		dec := codec.NewDecoderBytes(msg.Data, new(codec.MsgpackHandle))
		if err := dec.Decode(&data); err != nil {
			logger.Fatal(err)
		}

		ret := codec.NewEncoderBytes(&response, new(codec.MsgpackHandle))

		switch data["cmd"] {
		case "startbackup":
			if backupIsRunning() {
				ret.Encode(simpleRet{AgentID: agentid, Ret: "failed"})
				msg.Respond(response)

			} else {

				pid := startBackup(data["mode"])
				logger.Println(fmt.Sprintf("Backup started with pid %d", pid))

				p, _ := ps.Process(pid)
				info, _ := p.Info()

				ret.Encode(backupRet{AgentID: agentid, Ret: "success", Pid: pid, Name: info.Name, Cmdline: info.Args})
				msg.Respond(response)

			}
		case "info":
			ret.Encode(infoRet{Ret: "success", AgentID: agentid, Procs: getProcs()})
			msg.Respond(response)

		case "ping":
			payload := fmt.Sprintf("%s pong", agentid)
			ret.Encode(pongRet{Ret: "success", AgentID: agentid, Payload: payload})
			msg.Respond(response)

		case "halt":
			logger.Println("Shutting down")
			ret.Encode(simpleRet{Ret: "success", AgentID: agentid})
			msg.Respond(response)

			nc.Flush()
			nc.Close()
			os.Exit(0)
		}
	})
	nc.Flush()

	if err := nc.LastError(); err != nil {
		log.Fatal(err)
	}

	runtime.Goexit()
}

func getAgentID() string {
	out, _ := exec.Command("wmic", "csproduct", "get", "uuid").Output()
	hostname, _ := os.Hostname()
	uid := strings.Split(string(out), "\n")[1]
	uid = strings.TrimSpace(uid)

	return fmt.Sprintf("%s|%s", hostname, uid)
}

func startBackup(mode string) int {
	veeam := filepath.Join(os.Getenv("PROGRAMFILES"), "Veeam\\Endpoint Backup", veeamExe)
	cmd := exec.Command(veeam, mode)
	cmd.Start()

	return cmd.Process.Pid
}

func backupIsRunning() bool {

	procs, _ := ps.Processes()

	for _, proc := range procs {
		p, _ := proc.Info()
		if p.Name == veeamExe {
			return true
		}
	}
	return false
}

func getProcs() procList {
	ret := make([]proc, 0)

	procs, _ := ps.Processes()

	for _, process := range procs {
		p, _ := process.Info()
		if p.Name == veeamExe {

			var i = proc{
				p.Name,
				p.PID,
				p.PPID,
				p.Args,
			}
			ret = append(ret, i)
		}
	}
	return ret
}

func setupLogging() {
	debuglog, _ = os.OpenFile("backupagent.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	logger = log.New(debuglog, "", log.LstdFlags)
}

func setupConnOptions(opts []nats.Option) []nats.Option {
	opts = append(opts, nats.ReconnectWait(time.Second*5))
	opts = append(opts, nats.RetryOnFailedConnect(true))
	opts = append(opts, nats.MaxReconnects(-1))
	return opts
}
