pyobs
=====

http://www.pyobs.org/


Quick start
-----------

Create a directory and a virtual environment:

    mkdir test
    cd test
    python3 -m venv venv

Activate environment and install pyobs-core:

    ./venv/bin/activate
    pip3 install pyobs-core
    
Create a test configuration test.yaml:

    class: pyobs.modules.test.StandAlone
    message: Hello world
    interval: 10
      
And run it:
   
    pyobs test.yaml
