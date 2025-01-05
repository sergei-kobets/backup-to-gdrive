#!/usr/bin/env python3

import sys, tarfile, os.path, getopt, json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive.metadata"]
creds = None
source_dir = ''
gdrive_backup_dir = ''
files_count = 0


def main():
    check_args()
    check_token()
    filename = generate_tar_filename()
    tar_files(filename)
    upload_tar(filename)
    rm_local_tar_file(filename)

    print('The backup has been successfully uploaded!')
    exit(0)


def rm_local_tar_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def check_args():
    global source_dir
    global gdrive_backup_dir
    global files_count

    argument_list = sys.argv[1:]
    options = "s:g:f:"

    try:
        optlist, args = getopt.getopt(argument_list, options)
    except getopt.GetoptError as err:
        print(err)
        exit(1)

    for opt in optlist:

        if opt[0]:
            if not opt[1]:
                print('The value of option {} is not defined.'.format(opt[0]))
                exit(1)
            if opt[0] == "-s":
                source_dir = str(opt[1])
            elif opt[0] == "-g":
                gdrive_backup_dir = str(opt[1])
            elif opt[0] == "-f":
                files_count = int(opt[1])

    if not source_dir:
        print('The source directory ("-s") is not defined.')
        exit(1)
    if not gdrive_backup_dir:
        print('The gdrive directory ("-g") is not defined.')
        exit(1)


def generate_token():
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    print('Please go to this URL: {}'.format(auth_url))
    code = input('Enter the authorization code: ')
    flow.fetch_token(code=code)

    return flow


def check_token():
    global creds

    if os.path.exists("token.json") and os.path.getsize("token.json") > 0:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = generate_token()
            creds = flow.credentials
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(flow.credentials.to_json())


def generate_tar_filename():
    now = datetime.now()
    return now.strftime('%d-%m-%Y:%H:%M:%S') + '.tar.gz'


def tar_files(file):
    global source_dir
    if not os.path.isfile(file):
        print("Archiving files, please wait...")
        with tarfile.open(file, 'w:gz') as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))

    print("The archiving process finished successfully!")


def get_backup_dir_id(service):
    global gdrive_backup_dir
    backup_dir_id = None
    results = (
        service.files()
        .list(fields="files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
        print("No files found in G-drive.")
        exit(1)
    for item in items:
        if item['name'] == gdrive_backup_dir:
            backup_dir_id = item['id']
            break

    return backup_dir_id


def remove_old_backups(service, backup_dir_id):
    global files_count
    count = 0
    if files_count > 0:
        try:
            files = service.files().list(orderBy="createdTime asc",
                                         q="'{}' in parents and trashed = false".format(backup_dir_id)).execute()
            count = len(files['files'])
        except HttpError as error:
            print(f"An error occurred: {error}")
            exit(1)
        if count >= files_count > 0:
            files_to_remove_count = count - files_count
            for file in files['files']:
                print('Remove old backup file: {}'.format(file['name']))
                service.files().delete(fileId=file['id']).execute()
                files_to_remove_count -= 1
                if files_to_remove_count <= 0:
                    break


def upload_tar(file):
    global creds

    try:
        service = build("drive", "v3", credentials=creds)
        backup_dir_id = get_backup_dir_id(service)

        if backup_dir_id:
            remove_old_backups(service, backup_dir_id)
            print('Uploading the backup to Google Drive now...')
            file_metadata = {"name": file, 'parents': [backup_dir_id]}
            media = MediaFileUpload(file, mimetype="application/gzip", resumable=True, chunksize=262144)
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        else:
            print("Backup directory id is not found.")
            exit(1)

    except HttpError as error:
        print(f"An error occurred: {error}")
        exit(1)


if __name__ == '__main__':
    main()
