#!/bin/bash

LIBFILES="$(find ./wct-pppoe -name '*.py' | tr '\n' ' ')"

autopep8 -ia --ignore=E501 ${LIBFILES}