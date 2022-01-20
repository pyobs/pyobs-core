pyobs
=====

http://www.pyobs.org/


Quick start
-----------

Install pyobs-core:

    pip3 install --user pyobs-core
    
Alternatively, create a virtual environment and install pyobs-core in there:

    python3 -m venv pyobs-venv
    source pyobs-venv/bin/activate
    pip3 install pyobs-core
    
Create a test configuration test.yaml:

    class: pyobs.modules.test.StandAlone
    message: Hello world
    interval: 10
      
And run it:
   
    pyobs test.yaml
