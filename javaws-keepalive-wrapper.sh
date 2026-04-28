#!/bin/sh
# OpenWebStart javaws wrapper.
#
# Workaround for a Dell iDRAC 7/8 HTTPS server bug: the iDRAC web server
# silently hangs on HTTP/1.1 connection reuse — when Java sends a HEAD
# request for one resource and a GET on the same kept-alive TLS
# connection (which OpenWebStart's parallel resource downloader does
# routinely), the second request never receives a response and times out
# at the JNLP runtime's read-timeout. Forcing http.keepAlive=false makes
# Java open a fresh TCP/TLS connection per resource, sidestepping the
# bug. http.maxConnections=1 limits the connection pool to reinforce
# single-shot semantics.
#
# This wrapper is invoked transparently in place of the upstream javaws
# binary (the real one is shipped at $OWS_DIR/javaws.real). It is a no-op
# on hardware whose HTTPS server handles keep-alive correctly.

OWS_DIR=/opt/OpenWebStart

# Ensure -Dhttp.keepAlive is on the user's OWS argument whitelist so the
# JNLP runtime accepts it. OWS only forwards JVM args from JAVAWS_VM_ARGS
# whose property names appear in either its built-in allow list or the
# user's deployment.jvm.arguments.whitelist. Append idempotently — never
# clobber an existing whitelist line.
if [ -n "${HOME-}" ] && [ -d "${HOME-}" ]; then
    DEPDIR="${HOME}/.config/icedtea-web"
    DEPFILE="${DEPDIR}/deployment.properties"
    mkdir -p "$DEPDIR" 2>/dev/null
    if [ ! -e "$DEPFILE" ] || ! grep -qs '^deployment\.jvm\.arguments\.whitelist=.*-Dhttp\.keepAlive' "$DEPFILE"; then
        printf 'deployment.jvm.arguments.whitelist=-Dhttp.keepAlive,-Dhttp.maxConnections\n' >> "$DEPFILE"
    fi
fi

# Append our two args to JAVAWS_VM_ARGS without dropping any user-provided
# ones. OWS reads this env var and forwards each whitelisted property to
# the spawned JNLP runtime's command line.
JAVAWS_VM_ARGS="${JAVAWS_VM_ARGS:+$JAVAWS_VM_ARGS }-Dhttp.keepAlive=false -Dhttp.maxConnections=1"
export JAVAWS_VM_ARGS

exec "$OWS_DIR/javaws.real" "$@"
