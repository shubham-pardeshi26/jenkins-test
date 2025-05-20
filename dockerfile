# Dockerfile

FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for SQLite
RUN apk add --no-cache sqlite-libs build-base

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to make the final image smaller
RUN apk del build-base

# Copy the application code and the entrypoint script into the container
COPY main.py .
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose port 8000 (where Uvicorn will run)
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]