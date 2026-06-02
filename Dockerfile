# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy just the requirements first (helps with caching)
COPY requirements.txt .

# 4. Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your e-commerce app code into the container
COPY . .

# 6. Expose the port Gunicorn will run on
EXPOSE 8000

# 7. The command to run your app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8000", "ecom_app:app"]
