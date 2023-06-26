FROM python:3.10-slim

COPY src/functions/dataload/ .
COPY src/layers/models/python/ .
COPY src/layers/utils/python/ .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "lambda.py"]
