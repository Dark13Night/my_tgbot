FROM python:3.11.8
WORKDIR /bot

COPY requirements.txt .
RUN pip install -r requirements.txt 
RUN apt-get update


COPY bot.py .

CMD ["python3", "bot.py"]
