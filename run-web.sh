#!/bin/sh

if test x"$NEW_RELIC_LICENSE_KEY" != x"" -o x"$NEW_RELIC_CONFIG_FILE" != x""
then
    newrelic-admin run-program waitress-serve --port=$PORT dyndns53:app
else
    waitress-serve --port=$PORT dyndns53:app
fi
