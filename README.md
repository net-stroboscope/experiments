# experiments
This repository contains labs and benchmarking scripts

## benchmarks

These are the scripts that were used to benchmarks the various algorithms:
  - The Key-Points Sampling
  - The Surrounding
  - The various scheduling pipelines.

It also contains the scripts to generate the paper graphs.

Execute these scripts as part of a python module, e.g.:
`python -m benchmarks.bench_ilp [optional arguments]`


## labs

This directory contains sample labs, i.e. emulated topologies.

These labs use [ipmininet](https://github.com/oliviertilmans/ipmininet)
in order to spawn OSPF networks and reconstruct the graph.

## virtual-machine

This direction contains the Vagrantfile to build and manage a virtual machine
in which the labs can be run. This requires to have [Vagrant](vagrantup.com)
setup on your machine, as well as [VirtualBox](virtualbox.org) if you use the
default VM hypervisor.
