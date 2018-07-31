#!/usr/bin/env bash

set -e;

DJANGO_SETTINGS_MODULE=conf.settings.testing

if [ $BUILD = "TESTS" ]; then
    sh scripts/tests.sh;
elif [ $BUILD = "LINT" ]; then
    sh scripts/pycodestyle.sh;
    sh scripts/pylint.sh;
    npm run jsc;
fi
