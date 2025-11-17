# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install the system-level tools needed for compiling libraries like 'blis'
# This is the "toolbox" we were missing
RUN apt-get update && apt-get install -y build-essential

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# This will now succeed because build-essential is installed
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Tell Docker how to run your application
# This uses the gunicorn server you already have in requirements.txt
CMD ["gunicorn", "app:app"]
