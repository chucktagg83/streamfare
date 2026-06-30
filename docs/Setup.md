# StreamFare Development Setup

## Prerequisites

### Install the following software before running the project:

Python 3.13+
Git
Visual Studio Code
Microsoft Excel (optional, for editing the movie spreadsheet)
Clone the Repository
git clone <repository-url></repository>
cd streamfare
Create a Virtual Environment

#### Windows:

python -m venv streamfare

#### Activate:

streamfare\Scripts\activate

### Install Dependencies

pip install django
pip install pandas
pip install openpyxl

#### Or install everything from:

pip install -r requirements.txt
Apply Database Migrations
python manage.py makemigrations
python manage.py migrate
Create an Administrator
python manage.py createsuperuser
Start the Development Server
python manage.py runserver

### Open:

http://127.0.0.1:8000/

#### Admin:

http://127.0.0.1:8000/admin/
Import Movie Data

### Place the Excel spreadsheet in the project root directory:

streamfare/
    manage.py
    movies.xlsx

### Run the custom import command:

python manage.py import_movies

#### The importer will:

Read the Excel spreadsheet.
Validate each movie record.
Handle blank values appropriately.
Save movie records into the SQLite database.
Project Structure
streamfare/
│
├── manage.py
├── db.sqlite3
├── movies.xlsx
├── README.md
├── docs/
│
├── streamfare/
├── accounts/
├── home/
└── movies/
Current Dependencies
Django
Pandas
OpenPyXL
Current Project Status

✅ Django project configured

✅ Applications created

✅ Database configured

✅ Movie model completed

✅ Django Admin configured

✅ Custom Excel import command completed

✅ Movie library successfully imported

## Next Development Goals

Build the movie listing page.
Add movie detail pages.
Implement search and filtering.
Integrate movie metadata (posters, actors, descriptions, ratings).
Add secure user authentication.
Stream MP4 files through the web application.