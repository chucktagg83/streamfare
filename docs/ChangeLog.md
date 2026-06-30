
# Changelog

All notable changes to the StreamFare project will be documented in this file.

---

## Version 0.1.0 - June 30, 2026

### Project Initialization

* Created Django project **StreamFare**
* Configured Python virtual environment
* Installed Django and project dependencies
* Initialized Git repository
* Configured Git user information
* Created initial GitHub repository

### Applications

* Created **Home** application
* Created **Accounts** application
* Created **Movies** application
* Registered all applications in `<span>INSTALLED_APPS</span>`

### Database

* Designed the initial `<span>Movie</span>` model
* Added movie fields:
  * Title
  * Release Year
  * Rating
  * Length
  * Genre
  * Director
  * Cast
  * IMDb Rating
  * Format
  * Collection
* Created and applied database migrations
* Registered the Movie model with the Django Admin

### Excel Import

* Installed **Pandas**
* Installed **OpenPyXL**
* Created a custom Django management command:
  * `<span>import_movies</span>`
* Imported movie data from an Excel spreadsheet into the SQLite database
* Implemented handling for blank (NaN) spreadsheet values
* Verified imported movie records in the Django Admin

### Bug Fixes

* Corrected Django custom management command folder structure
* Fixed missing `<span>__init__.py</span>` package files
* Corrected model naming inconsistencies
* Fixed import command model references
* Resolved duplicate import issue
* Corrected `<span>IntegerField</span>` configuration by removing invalid `<span>max_length</span>`
* Fixed empty Excel file issue
* Fixed Excel engine configuration using `<span>openpyxl</span>`
* Resolved missing database migration for `<span>imdb_rating</span>`
* Corrected handling of blank numeric values during import

### Current Status

* Django project successfully configured
* SQLite database operational
* Movie database populated from Excel
* Django Admin fully functional
* Ready to begin development of the movie browsing interface

