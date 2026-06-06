FROM coady/pylucene:latest

WORKDIR /app

RUN pip install flask beautifulsoup4 requests

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
