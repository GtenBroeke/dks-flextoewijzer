
FROM python:3.8

LABEL Author=DKS
LABEL version="1.0"

ENV PYTHONUNBUFFERED=FALSE
ENV PIP_DISABLE_PIP_VERSION_CHECK=TRUE

COPY . /code/
RUN pip install /code/

WORKDIR /code
