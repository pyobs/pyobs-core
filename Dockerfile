FROM python:3.6

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /pytel
WORKDIR /pytel
RUN python setup.py install

ENTRYPOINT ["bin/pytel", "/pytel.yaml"]