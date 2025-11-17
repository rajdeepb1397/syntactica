# Use the full Python 3.9 runtime as a parent image
# This is more robust than the "slim" version
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install the system-level tools needed for compiling libraries like 'blis'
RUN apt-get update && apt-get install -y build-essential

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Tell Docker how to run your application
CMD ["gunicorn", "app:app"]
