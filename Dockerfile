FROM python:3-alpine
RUN apk update && apk add bash && apk add curl
WORKDIR /usr/src/
COPY . .
RUN pip install -r ./requirements.txt
CMD ["python", "localisejs.py","--operation","push_translation","--phraseFile","abc.txt"]
