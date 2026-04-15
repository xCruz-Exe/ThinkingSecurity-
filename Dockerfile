FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port Flask uses
EXPOSE 7860

CMD ["python", "main.py"]
