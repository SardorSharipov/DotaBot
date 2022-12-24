FROM python:latest
RUN pip install pyTelegramBotAPI==4.8.0
RUN pip install aiohttp==3.8.3
RUN mkdir  -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app
CMD ["python", "main.py"]