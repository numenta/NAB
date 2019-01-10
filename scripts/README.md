
NAB scripts directory
---------------------

This directory contains some useful utility functions.

---
##### Plotting data and results using Jupyter notebook

 * Intstall Jupyter,pandas,numpy,plotly if not installed for python 2.7

``` 
python -m pip install jupyter
python -m pip install pandas
python -m pip install numpy
python -m pip install plotly
```

 * Run Jupyter notebook in **scripts** directory
 ```
 jupyter notebook
 ```
* Use `"Plot Data.ipynb"` template notebook to plot data from `../data` folder

* User `"Plot Result - numenta.ipynb"` temlplate to plot results from `../results` folder

 ---
##### Plotting results

Please see plot.py, particularly the comments at the end. This script uses
[plot.ly](http://plot.ly) so you need a (free) account and API key from there.
It can generate plotly graphs for the raw data, labels, and/or detections.

We used this script to generate the plots in the paper.  You will need to modify
some lines at the bottom of the script to plot specific NAB data and/or results
files.


##### Alternative data and results visualization

There is currently a simple and somewhat hacky data visualizer available, useful
in hand labeling datasets. To use it do the following:

First generate the list of data files and result files:

    cd /path/to/nab
    ls -1 data/*/*.csv | grep data > scripts/data_file_paths.txt
    ls -1 results/*/*/*.csv | grep results | grep -v test_results > scripts/results_file_paths.txt
    cd scripts
    ln -s ../data
    ln -s ../results

From the scripts directory, type:

    python -m SimpleHTTPServer 12345
 
Then, open Chrome (only works on Chrome!) and type this into the url window:

    localhost:12345/nab_visualizer.html
 
To view data, click on "look at data", click in query window and then
press RETURN key. This should show all the data files. You can also filter
the files by keyword with the query window; it will filter for filenames that
contain the (case-sensitive) entered characters.

To get a string of the timestamp at a data point, simply click on the data point.

To zoom in on a region of data, drag the cursor to highlight the section of
interest. To zoom back out, double-click the screen.

[CURRENTLY NOT WORKING]To view result files, click on "look at results" first
and then click in query window and then press RETURN key. This should show all
the data files.

