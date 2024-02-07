FROM python:3.10

RUN pip install --upgrade pip
RUN pip freeze > requirements.txt

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["echo", "'STARTE'"]
CMD ["flask", "-A", "src/projector_backend/app", "run", "--host", "0.0.0.0"]
#CMD ["flask -A src/projector_backend/app run --host 0.0.0.0"]
#CMD ["flask", "-A", "app/main", "run"]
