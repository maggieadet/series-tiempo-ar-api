#!/usr/bin/env bash

set -e;

DJANGO_SETTINGS_MODULE=conf.settings.testing

if [ $BUILD = "TESTS" ]; then
    ES_URLS='http://localhost:9200/' sh scripts/tests.sh;
elif [ $BUILD = "LINT" ]; then
    sh scripts/pycodestyle.sh;
    sh scripts/pylint.sh;
    npm run jsc;
fi
