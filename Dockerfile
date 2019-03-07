FROM python:3.6-stretch

# install pyobs
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN python setup.py install

# clean up
RUN rm -rf /src

# set entry point
ENTRYPOINT ["/usr/local/bin/pyobs", "/pyobs.yaml"]