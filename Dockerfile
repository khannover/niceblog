FROM zauberzeug/nicegui:latest
COPY ./*.py *.sh /app/
RUN pip install -U python-slugify pyyaml ua-parser user-agents pytz
WORKDIR /app
CMD ["python3", "main.py"]
