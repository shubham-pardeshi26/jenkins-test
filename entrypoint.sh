#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running database migrations/table creation for Uvicorn (non-persistent setup)..."
# Call the function to create tables
python -c 'from main import create_db_tables; create_db_tables()'

# Check the exit code of the previous command
if [ $? -ne 0 ]; then
    echo "Database table creation failed. Exiting."
    exit 1
fi

echo "Starting Uvicorn..."
# Now run Uvicorn. The --host and --port are important for Docker.
exec uvicorn main:app --host 0.0.0.0 --port 8000