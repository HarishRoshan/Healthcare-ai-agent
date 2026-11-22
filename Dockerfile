FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["python", "-m", "uvicorn", "healthcare_api:app", "--host", "0.0.0.0", "--port", "8001"]
