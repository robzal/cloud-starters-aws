FROM python:alpine
WORKDIR /usr/src

COPY cfn/template.yaml .
COPY src/lambdas/reports/ .
COPY src/layers/boto3/python/ .
COPY src/layers/custom/python/ .

RUN apk -uv add --no-cache sudo && \
    apk upgrade && \
    pip install --no-cache-dir awscli

ENTRYPOINT ["python", "lambda_function.py"]
