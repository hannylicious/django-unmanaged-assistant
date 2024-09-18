# Django Unmanaged Assistant

Django Unmanaged Assistant is a Django app that provides a management command to create database tables for unmanaged models in your Django
project.

This app is intended for use in local development environments where you have unmanaged models that need to be reflected in local databases.

## Features

- Automatically creates tables for unmanaged models in your Django project based on the model definitions
- Checks for existing tables and columns before attempting to create them
- Provides informative output about the actions taken (if ran using `-d` or `--detailed` flag)
- Warns about potential type mismatches between model fields and database columns (if ran using `-d` or `--detailed` flag)
- Supports multiple databases

## Additional Feature

- Create local database(s) command for your Django project (`create_databases`)

## Requirements

- Python 3.6+
- Django 3.2+

## Installation

1. Install the package using pip:

   ```
   pip install django-unmanaged-tables
   ```

2. Add `'django_unmanaged_assistant'` to your `INSTALLED_APPS` setting in your Django project's settings file:

   ```python
   INSTALLED_APPS = [
       ...
       'django_unmanaged_assistant',
       ...
   ]
   ```

## Usage

After installation, you can use the `create_unmanaged_tables` management command to create tables for your unmanaged models:

```
python manage.py create_unmanaged_tables
```

This command will:

1. Scan through all the locally installed apps in your Django project
2. Identify unmanaged models
3. Create tables for these models if they don't already exist
4. Check existing tables for missing columns and add them if necessary
5. Provide warnings about potential type mismatches between model fields and database columns (if ran using `-d` or `--detailed` flag)

## How it works

The `create_unmanaged_tables` command performs the following steps for each unmanaged model:

1. Checks if the table for the model exists in the database
2. If the table doesn't exist, it creates the table
3. If the table exists, it checks each field in the model:
    - If a column for the field doesn't exist, it adds the column
    - If the column exists, it compares the column type with the expected type from the model field
    - It provides warnings if there are potential type mismatches (if ran using `-d` or `--detailed` flag)

## Configuration

No additional configuration is required. The app uses your project's database configuration as defined in your Django settings.

## Limitations

- This app is intended for use with unmanaged models in a local environment only. It will not affect managed models in your project in any way.
- This app should never be used/ran in a staging/production environment as we assume any databases/schemas/tables already exist in those environments.
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