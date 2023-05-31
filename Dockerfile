FROM python:3.11.3

WORKDIR /app
COPY /flask_app /flask_app

RUN pip install --no-cache-dir -r /flask_app/requirements.txt

EXPOSE 5000

CMD ["python", "/flask_app/__init__.py"]