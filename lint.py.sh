#!/bin/bash

pip install --upgrade autopep8
autopep8 --exit-code --recursive --in-place --aggressive --aggressive .
