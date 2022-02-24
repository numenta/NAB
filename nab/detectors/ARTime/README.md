# ARTime Detector

This detector is maintained in a separate GitHub repository [ARTimeNAB](https://github.com/markNZed/ARTimeNAB.jl) and was developed in the Julia programming language.

To run this detector you must install the [JuliaCall](https://github.com/cjdoris/PythonCall.jl) module which is in requiremetns.txt in this directory, it can be installed using pip: `pip install -r requirements.txt`

This Python wrapper for ARTime will use JuliaCall to install Julia and the ARTime Julia package, when the ARTime detector is run using NAB.

From the root of NAB run the ARTime detector with: `python run.py -d ARTime --detect --optimize --score --normalize --skipConfirmation`


