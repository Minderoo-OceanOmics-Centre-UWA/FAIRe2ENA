#!/usr/bin/env python3
# Thanks to Olivia Nguyen for v1 of this script!
import subprocess
import sys
from pathlib import Path

FTP_HOST = "webin2.ebi.ac.uk"      # TEST FTP server
FTP_SUBDIR = ""                    # Optional subfolder
WEBIN_USER = ""
WEBIN_PASS = ""

from argparse import ArgumentParser

parser = ArgumentParser(description = 'Uploads fastq files to the ENA FTP server.')
parser.add_argument('--host', help = 'URL of the ftp host. Defaults to the test ftp.', default = FTP_HOST, required = True)
parser.add_argument('--subdir', help = 'Path of the data on the ftp. Usually a folder', default = FTP_SUBDIR, required = True)
parser.add_argument('--user', help = 'Webin username of the account uploading the data', default = WEBIN_USER, required = True)
parser.add_argument('--passw', help = 'Webin password of the account uploading the data', default = WEBIN_PASS, required = True)

args = parser.parse_args()
ftp_host = args.host
ftp_subdir = args.subdir
ftp_user = args.user
ftp_pass = args.passw

def upload_files(file_path):
    remote_path = f"ftp://{ftp_host}/" + (ftp_subdir.strip('/') + '/' if ftp_subdir else '')

    cmd = [
        "curl",
        "-T", file_path,
        "-u", f"{ftp_user}:{ftp_pass}",
        remote_path
    ]

    print(f"Uploading {file_path} → {remote_path}")

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        print(f"Upload failed for {file_path}")
        sys.exit(1)
    print(f"Uploaded: {file_path}")


def main():
    print('Assuming files end in fastq.gz')

    all_files = sorted([str(f) for f in Path(".").glob("*.fastq.gz")])
    print('Found files: ' + '\n'.join(all_files))

    print(f"Uploading {len(all_files)} file(s) to ENA TEST FTP ({ftp_host})\n")
    if not all_files:
        print("No files listed. Please add files to READ_FILES or ASSEMBLY_FILES blocks.")
        sys.exit(1)

    print(f"Uploading {len(all_files)} file(s) to ENA TEST FTP ({ftp_host})\n")

    for f in all_files:
        upload_files(f)

    print("\nAll uploads complete.")
    if ftp_host == FTP_HOST:
        print("Files are now in your ENA TEST upload area:")
        print(f"ftp://{ftp_host}//{ftp_subdir if ftp_subdir else ''}")
        print("\nℹ️  Note: Files on the TEST server are automatically deleted within 24 hours.")
    else:
        print('Files are now in your ENA upload area:')
        print(f"ftp://{ftp_host}//{ftp_subdir if ftp_subdir else ''}")

if __name__ == "__main__":
    main()
