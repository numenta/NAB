## [HTM Java](https://github.com/numenta/htm.java) NAB detector

### Option 1: Run [htm.java](https://github.com/numenta/htm.java) with NAB on your local machine

First make sure you have __java 8__ installed

    java -version

Build __htm.java__ NAB detector:
    
    cd nab/detectors/htmjava
    ./gradlew clean build

Run __htm.java__ NAB detector:
    
    cd /path/to/nab
    python run.py -d htmjava --detect --optimize --score --normalize


### Option 2: Run [htm.java](https://github.com/numenta/htm.java) with NAB using provided [Dockerfile.htmjava](../../../Dockerfile.htmjava)

    cd /path/to/nab
    docker build -f Dockerfile.htmjava -t nab:htmjava .
    docker run --rm nab:htmjava
