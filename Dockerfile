FROM python:3.7.5
#ENV KUBECONFIG=/usr/src/app/.kube/config
RUN mkdir -p /usr/src/app/.kube
#COPY kubeconfig /usr/src/app/.kube/config
#COPY ca.crt /ca.crt
#COPY client.crt /client.crt
#COPY client.key /client.key
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY . /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt
RUN env
CMD ["python", "startApp.py"]