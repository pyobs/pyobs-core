pyobs
=====

Quick start
-----------

Clone the repository:

    git clone https://github.com/thusser/pytel-core.git
    cd pytel-core

Create a virtual environment (or skip this step if you want to have pyobs available globally):

    python3 -m venv venv
    source venv/bin/activate
    
Install dependencies:

    pip install -r requirements
    
Install pyobs:

    python setup.py install

Create a test configuration test.yaml:

    class: pyobs.Application

    module:
      class: pyobs.modules.test.StandAlone
      message: Hello world
      interval: 10
      
And run it:
   
    pyobs test.yaml
