## Install on Amazon Linux 64 bit
sudo yum update
sudo yum groupinstall "Development Tools"
sudo yum install cmake
sudo yum install zlib-devel
sudo yum install git

# install python 2.7 and change default python symlink 
sudo yum install python27-devel -y 
sudo rm /usr/bin/python
sudo ln -s /usr/bin/python2.7 /usr/bin/python 

# yum still needs 2.6, so write it in and backup script 
sudo cp /usr/bin/yum /usr/bin/_yum_before_27 
sudo sed -i s/python/python2.6/g /usr/bin/yum 
sudo sed -i s/python2.6/python2.6/g /usr/bin/yum 

# should display now 2.7.5 or later: 
python -V 

# now install pip for 2.7 
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py

# Clone NAB
git clone https://github.com/numenta/NAB.git

# Now install the rest of the requirements
sudo pip install -r NAB/requirements.txt


#####
# CentOS

sudo yum update
sudo yum install nano
sudo yum install nupic-py27-numenta
export PYTHONPATH=$PYTHONPATH:/opt/numenta/nupic/