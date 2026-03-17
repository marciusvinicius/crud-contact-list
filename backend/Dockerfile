FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install -r requirements.txt

ADD backend/ /app/backend

RUN chmod +x backend/entrypoint.sh

CMD ["backend/entrypoint.sh"]