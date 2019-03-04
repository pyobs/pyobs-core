FROM python:3.6-stretch

# install pytel
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN python setup.py install

# clean up
RUN rm -rf /src

# set entry point
ENTRYPOINT ["bin/pytel", "/pytel.yaml"]