# backup-to-gdrive
A simple script to back up data to Google Drive.

# prerequisite

* Enable google drive api: https://developers.google.com/drive/api/quickstart/python
* Oauth consent screen must have only one added scope: ".../auth/drive.file"
* Oauth consent screen must have at least one test user which will get access to the drive (the user can be same as gcp account/email)
* The "credentials.json" file (OAuth 2.0) from gcp must be added into the root dir of the project
* All python dependencies & virtual environment must be installed & configured
* Create Google Drive folder for backup files e.g. backups-folder

# script options
* Execute the script with following options:
  - "-s" => backup directory
  - "-g" => Google Drive folder name to store the backup
  - "-f" => (optional) max amount of stored backups. If the amount reach the number then oldest backup file will be removed
  
# usage example

```
cd /project/dir && ./bin/python3 main.py -s /home/test-user/my-dir-to-backup -g backups-folder -f 5
```

* First time execution ask for a token generation:
![1.png](screenshots%2F1.png)
* Open URL and use added cgp test account (e.g example@gmail.com), select all scopes and click "continue":
![2.png](screenshots%2F2.png)
* Copy auth code and paste into script & click enter:

![3.png](screenshots%2F3.png)

![4.png](screenshots%2F4.png)

The token.json will be generated and used next time.