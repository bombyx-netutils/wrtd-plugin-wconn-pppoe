#!/bin/bash

LIBFILES="$(find ./wct_pppoe -name '*.py' | tr '\n' ' ')"

autopep8 -ia --ignore=E501 ${LIBFILES}
