FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . /app

# Make entrypoinnt executable
RUN chmod +x /app/entrypoint.sh

ENV PORT=8000
EXPOSE 8000

# CMD ["gunicorn","run:app","-w","4","-b","0.0.0.0:8000","--log-file","-"]
CMD ["/app/entrypoint.sh"]