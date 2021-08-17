FROM python:3.7.5
RUN mkdir -p /usr/src/app/.kube
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY . /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt
RUN env
CMD ["python", "startApp.py"]