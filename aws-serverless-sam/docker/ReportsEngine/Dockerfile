FROM python:alpine
WORKDIR /usr/src

COPY template.yaml .
COPY lambdas/reports/ .
COPY layers/boto3/python/ .
COPY layers/custom/python/ .

RUN apk -uv add --no-cache sudo && \
    apk upgrade && \
    pip install --no-cache-dir awscli

ENTRYPOINT ["python", "lambda_function.py"]
