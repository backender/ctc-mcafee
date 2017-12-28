from python:3

MAINTAINER mail@marcjuch.li


COPY . /app
WORKDIR /app

RUN pip install pipenv

RUN pipenv install --system

RUN apt-get update && apt-get install -y \
  tesseract-ocr

RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader averaged_perceptron_tagger

CMD ["python", "main.py"]
