# Django Unmanaged Assistant

Django Unmanaged Assistant is a Django app that provides a management command 
to create database tables for unmanaged models in your Django
project.

This app is intended for use in local development environments where you have 
unmanaged models that need to be reflected in the local database(s).

This app is in an alpha state - meaning it is still in development and may 
have bugs or issues. Please use with caution and report any issues you 
encounter.

## Problem

When working with Django, you may have unmanaged models in your project whose
tables are not automatically created in the database. This can be problematic
when you need to work with these models in your local environment.

You may or may not have scripts to create these tables, but it can be 
cumbersome to manage these scripts and ensure they are up-to-date with your 
models.

## Solution

Instead of trying to 'make the models managed when running locally', which is 
commonly suggested (and thus possibly creating/committing migrations you do 
not want in your repo), you can use Django Unmanaged Assistant to dynamically 
create tables for your unmanaged models. 

Then you can use something like 'factory_boy' or other scripts to help 
generate data for these tables if you need dummy data, or leave them blank.

The app scans through all locally installed apps in your Django project, 
identifies unmanaged models, and creates tables for these models if they
don't already exist. It also checks existing tables for missing columns and 
adds them if necessary.

This app is designed primarily to give you a quick/easy way to create tables 
locally for unmanaged models in your local database(s) without having to 
manually create them or manage scripts for the creation of those tables/views.

## Features

- Automatically creates tables for unmanaged models in your Django project based on the model definitions
- Checks for existing tables and columns before attempting to create them
- Provides informative output about the actions taken (if ran using `-d` or `--detailed` flag)
- Warns about potential type mismatches between model fields and database columns (if ran using `-d` or `--detailed` flag)
- Supports multiple databases

## Additional Features

- Create local database(s) command for your Django project (`create_databases`)
  - This might be useful if you have multiple databases in your Django project and need to create them locally if they don't already exist.

## Requirements 

These are most likely already handled by your Django project, but just in case:

- Python 3.6+
- Django 3.2+
- psycopg2 / psycopg2-binary (if using PostgreSQL)
- mssql-django (if using Microsoft SQL Server)
- pyodbc (if using Microsoft SQL Server)
- The MSSQL ODBC driver installed on the OS (if using Microsoft SQL Server)

## Installation

1. Install the package using pip:

   ```
   pip install django-unmanaged-assistant
   ```

2. Add `'django_unmanaged_assistant'` to your `INSTALLED_APPS` setting in your 
Django project's settings file:

   ```python
   INSTALLED_APPS = [
       ...
       'django_unmanaged_assistant',
       ...
   ]
   ```
   
3. Optional: Add the following to your `settings.py` file to exclude apps that 
have a path containing the specified string:
   - By default, the app will exclude any apps that have a path containing 'site-packages' (i.e., pip-installed packages).
   - These are strings that are checked against the path of the app. If the path contains the string, the app is excluded from the scan.

    ```python
    EXCLUDE_UNMANAGED_PATH = 'path/to/exclude'  # default: 'site-packages'
    ```

4. Optional: Add the following to your `settings.py` file to map apps with 
unmanaged models to the appropriate database:

    ```python
    APP_TO_DATABASE_MAPPING = {"app": "default", "other_app": "additional_database"}
    ```

5. Optional: Add the following to your `settings.py` file to include unmanaged models from pip-installed packages:
   - Specify specific app names that you want to include in the scan (i.e., pip-installed packages).
   
    ```python
    ADDITIONAL_UNMANAGED_TABLE_APPS = ['app_name']
    ```

## Multiple Databases

If you have multiple databases in your Django project, you can add the following to your `settings.py` file:

There are currently no checks regarding custom dbrouters, so if you have a custom dbrouter, you may need to adjust the code to accommodate your setup.

```python
APP_TO_DATABASE_MAPPING = {"app": "default", "other_app": "additional_database_alias"}
```
This will allow us to make sure we create the apps model tables in the correct database.

## Additional pip-installed packages

By default, the app will only scan through locally installed apps in your Django project. Any app inside the virtual environment (if available) will not be scanned.

Should you want to have unmanaged models from a pip-installed package, you can add the following to your `settings.py` file:

```python
ADDITIONAL_UNMANAGED_TABLE_APPS = ['app_name']
```

## Usage

After installation and after the migration of your managed models with migrations, you can use the `create_unmanaged_tables` management command to create tables for your unmanaged models:

```
python manage.py create_unmanaged_tables
```

This command will:

1. Scan through all the locally installed apps in your Django project
2. Identify unmanaged models
3. Create tables for these models if they don't already exist
4. Check existing tables for missing columns and add them if necessary
5. Provide warnings about potential type mismatches between model fields and database columns (if ran using `-d` or `--detailed` flag)

## Assumptions

The app assumes that you have already created the database(s) in your local environment. 
   - If you haven't created the database(s) yet, you can use the `create_databases` command to create them:

The app assumes you have migrated all of your managed models already.

The app assumes two different styles of naming convention for your tables. If you have a different naming convention, you can reach out to us to see if we can help accommodate your style, or you can submit a Pull Request with the changes.
1. Unbracketed: `schema.table_name`
2. Bracketed: `[schema].[table_name]`

## How it works

The `create_unmanaged_tables` command performs the following steps for each unmanaged model:

1. Checks if the table for the model exists in the database
2. If the table doesn't exist, it creates the table
3. If the table exists, it checks each field in the model:
    - If a column for the field doesn't exist, it adds the column
    - If the column exists, it compares the column type with the expected type from the model field
    - It provides warnings if there are potential type mismatches (if ran using `-d` or `--detailed` flag)

## Configuration

Install the app and add it to your `INSTALLED_APPS` setting in your Django project's settings file.

You can also configure the app by adding the following to your `settings.py` file:

- `EXCLUDE_UNMANAGED_PATH`: A string that is checked against the path of the app. If the path contains the string, the app is excluded from the scan. Default: 'site-packages'
- `APP_TO_DATABASE_MAPPING`: A dictionary that maps apps with unmanaged models to the appropriate database. Default: 'default'
- `ADDITIONAL_UNMANAGED_TABLE_APPS`: A list of app names that you want to include in the scan. Default: []

## Supported Databases

The app supports the following databases:

- SQLite (alpha stages)
- PostgreSQL (alpha stages)
- Microsoft SQL Server (alpha stages)

If you would like to add support for additional databases, please feel free to submit a Pull Request!

## Limitations

- This app is intended for use with unmanaged models in a local environment only. It will not affect managed models in your project in any way.
- This app should NEVER be used/ran in a staging/production environment as we assume any databases/schemas/tables already exist in those environments.
- While the app attempts to create appropriate database schema, complex model relationships or custom field types may require manual
  intervention.
- The app provides warnings about potential type mismatches, but it does not automatically alter existing column types. Such changes should
  be handled manually to prevent data loss.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Support

If you encounter any problems or have any questions, please open an issue on the GitHub repository.

Django Unmanaged Assistant is free and always will be. It's developed and maintained in an Open Source manner. Any support is greatly appreciated.
