//go:generate goversioninfo -icon=onit.ico -manifest=goversioninfo.exe.manifest -gofile=versioninfo.go
package main

import (
	"flag"
	"fmt"
	nats "github.com/nats-io/nats.go"
	"github.com/shirou/gopsutil/process"
	"github.com/ugorji/go/codec"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

var (
	debuglog *os.File
	logger   *log.Logger
	endpoint string
	token    string
	version  = "1.2.0"
)

type proc struct {
	Name    string   `json:"name"`
	Pid     int32    `json:"pid"`
	Ppid    int32    `json:"ppid"`
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

		if data["cmd"] == "startbackup" {

			if backupIsRunning() {

				ret := codec.NewEncoderBytes(&response, new(codec.MsgpackHandle))
				ret.Encode(simpleRet{AgentID: agentid, Ret: "failed"})
				msg.Respond(response)

			} else {

				pid := startBackup(data["mode"])
				logger.Println(fmt.Sprintf("Backup started with pid %d", pid))

				p, _ := process.NewProcess(int32(pid))
				name, _ := p.Name()
				cmdline, _ := p.CmdlineSlice()

				ret := codec.NewEncoderBytes(&response, new(codec.MsgpackHandle))
				ret.Encode(backupRet{AgentID: agentid, Ret: "success", Pid: pid, Name: name, Cmdline: cmdline})
				msg.Respond(response)

			}
		} else if data["cmd"] == "info" {

			procs := getProcs()

			ret := codec.NewEncoderBytes(&response, new(codec.MsgpackHandle))
			ret.Encode(infoRet{Ret: "success", AgentID: agentid, Procs: procs})
			msg.Respond(response)

		} else if data["cmd"] == "ping" {

			payload := fmt.Sprintf("%s pong", agentid)
			ret := codec.NewEncoderBytes(&response, new(codec.MsgpackHandle))
			ret.Encode(pongRet{Ret: "success", AgentID: agentid, Payload: payload})
			msg.Respond(response)

		} else if data["cmd"] == "halt" {

			logger.Println("Shutting down")

			ret := codec.NewEncoderBytes(&response, new(codec.MsgpackHandle))
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
	veeam := filepath.Join("C:\\Program Files\\Veeam\\Endpoint Backup", "Veeam.EndPoint.Manager.exe")
	cmd := exec.Command(veeam)
	cmd.Start()

	return cmd.Process.Pid
}

func backupIsRunning() bool {
	pids, _ := process.Pids()

	for _, pid := range pids {
		p, _ := process.NewProcess(pid)
		name, _ := p.Name()

		if name == "Veeam.EndPoint.Manager.exe" {
			return true
		}
	}

	return false
}

func getProcs() procList {
	ret := make([]proc, 0)
	pids, _ := process.Pids()

	for _, pid := range pids {

		p, _ := process.NewProcess(pid)
		name, _ := p.Name()
		pid := p.Pid
		ppid, _ := p.Ppid()
		cmdline, _ := p.CmdlineSlice()

		if name == "Veeam.EndPoint.Manager.exe" {
			var i = proc{
				name,
				pid,
				ppid,
				cmdline,
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
