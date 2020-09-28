// go build -ldflags="-X 'main.RsyncHost=sshuser@example.com'" tacticaloffsite.go
package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
)

var (
	Version   = "1.1.0"
	RsyncHost string
)

func doRsync(source string, dest string, limit int, logfile *os.File, ext string) (err error) {

	rsyncArgs := []string{
		"-havz", "--progress", fmt.Sprintf("--bwlimit=%d", limit),
		"--partial-dir=.rsync-partial", fmt.Sprintf("--include='*.%s'", ext),
		"--exclude='*'", source, fmt.Sprintf("%s:%s", RsyncHost, dest),
	}

	cmd := exec.Command("rsync", rsyncArgs...)
	cmd.Stdout = logfile
	cmd.Stderr = logfile

	err = cmd.Start()
	if err != nil {
		fmt.Println(err)
	}

	err = cmd.Wait()
	if err != nil {
		fmt.Println(err)
	}

	return nil

}

func main() {

	source := flag.String("source", "", "Source Dir")
	dest := flag.String("dest", "", "Destination Dir")
	limit := flag.Int("limit", 300, "bw limit in kb/s")
	logfile := flag.String("logfile", "", "Log file location")
	ver := flag.Bool("version", false, "Prints version")
	flag.Parse()

	if *ver {
		fmt.Println(Version)
		return
	}

	if len(os.Args) != 9 {
		fmt.Printf("Usage: %s source dest limit logfile\r\n", os.Args[0])
		os.Exit(1)
	}

	f, err := os.OpenFile(*logfile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Fatal(err)
		os.Exit(1)
	}
	defer f.Close()

	logger := log.New(f, "", log.LstdFlags)
	logger.Println("Offsite Started")

	// metadata, full backups, incremental backups
	veeams := []string{"vbm", "vbk", "vib"}

	for _, val := range veeams {
		err = doRsync(*source, *dest, *limit, f, val)
		if err != nil {
			log.Fatal(err)
			os.Exit(1)
		}
	}

	logger.Println("Offsite Finished")
	f.WriteString(fmt.Sprintf("%s\n", strings.Repeat("-", 100)))
}
