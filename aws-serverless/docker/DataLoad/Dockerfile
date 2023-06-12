FROM python:3.9-slim

COPY src/lambdas/dataload/ .
COPY src/layers/models/python/ .
COPY src/layers/utils/python/ .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "lambda.py"]
