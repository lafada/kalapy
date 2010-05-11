# Settings for tests project

# Name of the project
PROJECT_NAME = "tests"

# Version of the project
PROJECT_VERSION = "1.0"

# Database backend engine
# Possible value can be either sqlite3, postgresql, bigtable
DATABASE_ENGINE = "postgresql"

# Database name
# For sqlite3 use path to the sqlite3 database file
# For bigtable keep empty
DATABASE_NAME = "test_rapido"

# Database user (must have rights to create database tables)
# Keep empty for sqlite3 and bigtable
DATABASE_USER = ""

# Database password
# Keep empty for sqlite3 and bigtable
DATABASE_PASSWORD = ""

# Database host
# Keep empty for sqlite3 and bigtable
DATABASE_HOST = ""

# Database port
# Keep empty for sqlite3 and bigtable
DATABASE_PORT = ""

# Enable/Disable internationalization support
USE_I18N = True

# List of installed packages
INSTALLED_PACKAGES = (
    'db_core',
    'db_model',
)
