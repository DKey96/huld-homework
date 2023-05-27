# File System Manager Microservice

The File System Manager Microservice is a solution to an assessment with a goal to:
- Create a service, that would scan a predefined directory and send all the files inside to an external service via HTTPS.
- Files already sent or a duplicate files should be ignored, if run again

## Tech-stack

### Main dependencies

- Python 3.11
  - Django
  - DRF (Django Rest Framework)
  - Django split settings

Other libraries can be found in the `requirements.txt`.

## How to use

### Docker Environment

- As a part of the projects, there is a Dockerfile and docker-compose.yaml, so that the app can be run without 
need to setup the local environment. 
- Only necessary things to be install is [Docker](https://docs.docker.com/engine/install/).
- Then just navigate to the top folder and run:
```bash
docker-compose build && docker-compose up
```

### Local Environment

#### PostgreSQL Setup

- Creating the PostgreSQL Database and User
```bash
sudo -u postgres psql
```
```bash
CREATE DATABASE huld;
CREATE USER huld WITH PASSWORD 'huld';

ALTER ROLE huld SET client_encoding TO 'utf8';
ALTER ROLE huld SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE huld TO huld;
```
#### Django Setup

- Create a virtual environment and activate it
```bash
python3 -m venv venv
source /venv/bin/activate
```
- Install all necessary libraries
```bash
python3 -m pip install -r requirements.txt 
```
- Migrate the database (make sure you are in the `huld` folder)
```bash
python3 manage.py migrate 
```
- Start the application
```bash
python3 manage.py runserver 
```

### After your environment is ready and app running

- Open the URL of the application and press the button. This will scan the predefined folder and send all the files to the predefined URL.
  - Predefined folder can be specified inside the `settings/components/base.py` under `FILES_FOLDER_PATH` variable.
  - External service URL can be specified inside the `settings/components/base.py` under `FILE_RECEIVE_URL` variable.
- In addition, there are two methods, how to send the files to the external service.
  - One-by-by = Each file is send to the external service in one request. (Number of files = number of requests)
  - Bulk = All files are sent at once. (One request for all the files)
  - The option can be specified in the `settings/components/base.py` under `SEND_FILES_BULK` variable.

## Endpoints

- "/" -> Main Screen - Returns HTTP View (HTML)
  - Method: `GET`
  - Returns:
    - HTTPResponse with HTML
- "/transfer/" -> Endpoint for start of the file transfer over the HTTP request
  - Method: `POST`
  - Returns:
    - 200 - OK
    - 424 - Failed Dependency - Returned when the external URL service is unreachable or returns any response with statuses gte 400
- "/transfer/upload/"
  - Method: `POST`
  - Request:
    - JSON: {"file": File-to-be-uploaded}
  - Response:
    - 204 - OK
    - 400 - Bad Request - When the file, that was sent is invalid (empty or corrupted)