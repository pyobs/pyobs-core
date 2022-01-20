pyobs
=====

<p style="text-align: center">
  <a href="https://www.pyobs.org/">
    <img src="https://github.com/pyobs/pyobs-core/blob/master/docs/source/_static/pyobs.png?raw=True" 
         style="width: 50%; max-width: 500px"/><br/>
    http://www.pyobs.org/
  </a>
</p>


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
