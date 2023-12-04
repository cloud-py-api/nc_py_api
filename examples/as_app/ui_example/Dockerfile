FROM python:3.11-slim-bookworm

COPY requirements.txt /

COPY css /app/css
COPY img /app/img
COPY js /app/js
COPY l10n /app/l10n
COPY lib /app/lib

RUN \
  python3 -m pip install -r requirements.txt && rm -rf ~/.cache && rm requirements.txt

WORKDIR /app/lib
ENTRYPOINT ["python3", "main.py"]
