FROM python:3.11-slim-bookworm

COPY requirements.txt /

ADD /css /app/
ADD /img /app/
ADD /js /app/
ADD /l10n /app/
ADD /lib /app/

RUN \
  python3 -m pip install -r requirements.txt && rm -rf ~/.cache && rm requirements.txt

WORKDIR /app/lib
ENTRYPOINT ["python3", "main.py"]
