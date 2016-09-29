## [HTM Java](https://github.com/numenta/htm.java) NAB detector

##### Run [htm.java](https://github.com/numenta/htm.java) with NAB

First make sure you have __java 8__ installed

    java -version

Build __htm.java__ NAB detector:

    cd nab/detectors/htmjava
    ./gradlew clean build

Run __htm.java__ NAB detector:

    cd /path/to/nab
    python run.py -d htmjava --detect --score --normalize
