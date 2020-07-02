import subprocess
import argparse
import datetime as dt

__version__ = "1.0.1"

OFFSITE_DEST = "tactical@offsite.tacticaltechs.com"


def main():
    parser = argparse.ArgumentParser(description="Tactical Offsite Backup")
    parser.add_argument(
        "--source", action="store", dest="source", type=str, required=False
    )
    parser.add_argument(
        "--dest", action="store", dest="destination", type=str, required=False
    )
    parser.add_argument(
        "--limit", action="store", dest="limit", type=int, required=False
    )
    parser.add_argument(
        "--logfile",
        action="store",
        dest="logfile",
        type=str,
        required=False,
        help="The full path to the log file",
    )
    parser.add_argument(
        "--version", required=False, action="store_true", help="Prints version"
    )
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    # sync the metadata file first
    cmd1 = [
        "rsync",
        "-havz",
        "--progress",
        f"--bwlimit={args.limit}",
        "--partial-dir=.rsync-partial",
        "--include='*.vbm'",
        "--exclude='*'",
        args.source,
        f"{OFFSITE_DEST}:{args.destination}",
    ]
    # next, sync the full backups
    cmd2 = [
        "rsync",
        "-havz",
        "--progress",
        f"--bwlimit={args.limit}",
        "--partial-dir=.rsync-partial",
        "--include='*.vbk'",
        "--exclude='*'",
        args.source,
        f"{OFFSITE_DEST}:{args.destination}",
    ]
    # finally, sync the incremental backups
    cmd3 = [
        "rsync",
        "-havz",
        "--progress",
        f"--bwlimit={args.limit}",
        "--partial-dir=.rsync-partial",
        "--include='*.vib'",
        "--exclude='*'",
        args.source,
        f"{OFFSITE_DEST}:{args.destination}",
    ]

    started = dt.datetime.now().strftime("%b-%d-%Y_%I-%M-%S_%p")
    with open(args.logfile, "a+") as f:
        f.write(f"Offsite started at {started}\n")

    with open(args.logfile, "a+") as f:

        r1 = subprocess.run(cmd1, stdout=f, stderr=subprocess.STDOUT)
        r2 = subprocess.run(cmd2, stdout=f, stderr=subprocess.STDOUT)
        r3 = subprocess.run(cmd3, stdout=f, stderr=subprocess.STDOUT)

    finished = dt.datetime.now().strftime("%b-%d-%Y_%I-%M-%S_%p")
    with open(args.logfile, "a+") as f:
        f.write(f"\nOffsite finished at {finished}\n")
        f.write("-" * 100)
        f.write("\n")


if __name__ == "__main__":
    main()
