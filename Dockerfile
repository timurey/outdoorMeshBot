FROM python:3.9-slim
WORKDIR /app
RUN pip install meshtastic pubsub requests pytz
COPY bot.py .
COPY weather.py .
CMD ["python", "-u", "./bot.py", "--connection-type", "serial", "--serial-port", "/dev/ACM0", "--timezone", "Asia/Yekaterinburg"]