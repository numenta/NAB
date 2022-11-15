# ARTime Detector

This detector is maintained in a separate GitHub repository [ARTimeNAB](https://github.com/markNZed/ARTimeNAB.jl) and was developed in the Julia programming language.

To run this detector you must install the [JuliaCall](https://github.com/cjdoris/PythonCall.jl) Python module which is in requirements.txt in this directory, it can be installed using pip: `pip install -r requirements.txt`

This Python wrapper for ARTime will use JuliaCall to install Julia and the ARTime Julia package, when the ARTime detector is run using NAB.

JuliaCall will default to installing the latest stable version of Julia (ignoring the Julia version in the juliacalldeps.json file at the root of NAB). ARTime is no longer compatible with the most recent Julia language. To use Julia 1.7.0 with JuliaCall you must install Julia 1.7.0 and set the environment variable: PYTHON_JULIACALL_EXE to the Julia 1.7.0 binary executable before running the ARTime detector.

From the root of NAB run the ARTime detector with: `python run.py -d ARTime --detect --optimize --score --normalize --skipConfirmation`


