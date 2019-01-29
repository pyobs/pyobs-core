# pytel

## Installation

The easiest way for installing pytel on a production system is running "python setup.py install" for each module. 
Sometimes a more controlled environment with its own build directory is preferred, so here we go.

1. Create directories:
```bash
mkdir -p ~/pytel/src
```

2. Check out all the required modules from gitlab:
```bash
cd ~/pytel/src
git clone https://gitlab.gwdg.de/thusser/pytel pytel
git clone https://gitlab.gwdg.de/thusser/pytel-http pytel-http
```

3. Link the pull-and-build script:
```bash
cd ~/pytel
ln -s src/pytel/bin/pull_and_build.sh .
```

4. Build pytel:
```bash
cd ~/pytel
./pull_and_build.sh
```

5. Add pathes to ~/.bashrc:
```bash
# pytel
export PYTHONPATH=$PYTHONPATH:~/pytel/build/lib/python3.6/site-packages
export PATH=$PATH:~/pytel/build/bin
```
