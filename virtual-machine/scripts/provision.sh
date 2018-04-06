#!/bin/bash
pushd ~

progress() {
    echo "@@ $1"
}

clone() {
    progress "Cloning $2"
    if [[ -d "$1" ]]; then
        cd ${1}
        git pull
        cd ..
    else
        git clone --recursive "https://github.com/net-stroboscope/$1"
    fi
}

progress "Setting up root ssh login"
mkdir -p /root/.ssh
cat /home/vagrant/.ssh/authorized_keys >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

progress "Installing dependencies"
# We need non-free for snmp mibs
sed -i '/^deb /s/$/ non-free/' /etc/apt/sources.list
sudo apt-get -y -qq --force-yes update
sudo apt-get -y -qq --force-yes install git bridge-utils python bash \
                        python-dev python-pip gcc build-essential \
                        automake autoconf libtool gawk libreadline-dev \
                        texinfo tmux vim-nox xterm tcpdump emacs nano
update-inetd --comment-chars '#' --enable discard

progress "Installing Mininet"
git clone https://github.com/mininet/mininet.git
./mininet/util/install.sh -n
progress "Installing IPMininet"
pip install ipmininet

clone collector "the collector"
clone experiments "the experiments"

progress "Installing the collector"
pushd collector
pip install -e '.'
popd

progress ""
progress ""
progress "If you plan to use features such as Virtual Box shared folders, ..."
progress "You will need to rebuild the guest-additions !"
progress "Insert the guest addition CD from the VirtualBox GUI, then mount it"
progress 'in the vm (`mount +exec /dev/cdrom /mnt`), and run the file'
progress '`VBoxLinuxAdditions.run`'
popd
