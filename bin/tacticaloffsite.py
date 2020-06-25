import subprocess
import argparse
import datetime as dt

OFFSITE_DEST = "tactical@offsite.tacticaltechs.com"


def main():
    parser = argparse.ArgumentParser(description="Tactical Offsite Backup")
    parser.add_argument(
        "--source", action="store", dest="source", type=str, required=True
    )
    parser.add_argument(
        "--dest", action="store", dest="destination", type=str, required=True
    )
    parser.add_argument(
        "--limit", action="store", dest="limit", type=int, required=True
    )
    parser.add_argument(
        "--logfile",
        action="store",
        dest="logfile",
        type=str,
        required=True,
        help="The full path to the log file",
    )
    args = parser.parse_args()

    # first do all non .vbk files since those are largest, save for last
    cmd1 = [
        "rsync",
        "-havz",
        "--progress",
        f"--bwlimit={args.limit}",
        "--partial-dir=.rsync-partial",
        "--exclude='*.vbk'",
        args.source,
        f"{OFFSITE_DEST}:{args.destination}",
    ]

    cmd2 = [
        "rsync",
        "-havz",
        "--progress",
        f"--bwlimit={args.limit}",
        "--partial-dir=.rsync-partial",
        args.source,
        f"{OFFSITE_DEST}:{args.destination}",
    ]

    started = dt.datetime.now().strftime("%b-%d-%Y_%I-%M-%S_%p")
    with open(args.logfile, "a+") as f:
        f.write(f"Offsite started at {started}\n")

    with open(args.logfile, "a+") as f:

        r1 = subprocess.run(cmd1, stdout=f, stderr=subprocess.STDOUT)
        r2 = subprocess.run(cmd2, stdout=f, stderr=subprocess.STDOUT)

    finished = dt.datetime.now().strftime("%b-%d-%Y_%I-%M-%S_%p")
    with open(args.logfile, "a+") as f:
        f.write(f"\nOffsite finished at {finished}\n")
        f.write("-" * 100)
        f.write("\n")


if __name__ == "__main__":
    main()
