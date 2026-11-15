# openwebstart-rpm

Fedora/RPM packaging of [OpenWebStart](https://openwebstart.com/) — an
open-source successor to Oracle Java Web Start, used to launch `.jnlp`
files (notably Dell iDRAC virtual consoles, older Oracle apps, etc.).

This is a **binary repack** of the upstream `.deb` release published by
[Karakun AG](https://karakun.com/) at the
[karakun/OpenWebStart](https://github.com/karakun/OpenWebStart) repository.
A bundled Adoptium Temurin 11 runtime ships with the package, so
OpenWebStart operates independently of the system Java version.

## Install

A pre-built RPM is published via COPR:

```sh
sudo dnf copr enable twodcube/openwebstart
sudo dnf install openwebstart
```

If you have `icedtea-web` installed, dnf will offer to remove it — both
ship `/usr/bin/javaws`, and `icedtea-web` is unmaintained on Java 25+
anyway.

## What you get

| Path | Description |
|---|---|
| `/opt/OpenWebStart/` | Upstream payload, including bundled Temurin 11 runtime |
| `/usr/bin/javaws` | Wrapper that fixes the iDRAC keep-alive bug, then execs the real javaws |
| `/usr/bin/itw-settings` | OpenWebStart Control Panel (deployment.properties UI) |
| `/usr/share/applications/openwebstart.desktop` | MIME handler for `application/x-java-jnlp-file` |
| `/usr/share/mime/packages/openwebstart.xml` | MIME type definition for `.jnlp` |

After install, double-clicking a `.jnlp` from your file manager will route
through OpenWebStart automatically, and the bundled wrapper makes Dell
iDRAC virtual consoles work without any extra configuration.

## What the wrapper does

`/usr/bin/javaws` is a small POSIX shell script (see
[`javaws-keepalive-wrapper.sh`](javaws-keepalive-wrapper.sh)) that:

1. Idempotently appends `deployment.jvm.arguments.whitelist=-Dhttp.keepAlive,...`
   to `~/.config/icedtea-web/deployment.properties` so OpenWebStart's
   JNLP runtime accepts the property.
2. Exports `JAVAWS_VM_ARGS=-Dhttp.keepAlive=false -Dhttp.maxConnections=1`
   so OpenWebStart appends those flags to the spawned JNLP runtime's
   command line.
3. Hands off to `/opt/OpenWebStart/javaws.real`.

The fix exists because Dell iDRAC 7/8 HTTPS firmware silently hangs on
HTTP/1.1 connection reuse: a HEAD followed by a GET on the same
kept-alive TLS connection — exactly what OpenWebStart's parallel resource
downloader does — never gets a response. Forcing `http.keepAlive=false`
makes Java open a fresh TCP/TLS connection per resource, sidestepping
the bug.

The wrapper is a no-op for any HTTPS server that handles keep-alive
correctly. To opt out, set `JAVAWS_NO_KEEPALIVE_FIX=1` in your
environment or invoke `/opt/OpenWebStart/javaws.real` directly.

## Building locally

```sh
# Stage the upstream .deb where rpmbuild expects it
mkdir -p ~/rpmbuild/{SPECS,SOURCES}
cp openwebstart.spec ~/rpmbuild/SPECS/
cp openwebstart.desktop openwebstart-settings.desktop \
   openwebstart.xml javaws-keepalive-wrapper.sh ~/rpmbuild/SOURCES/
spectool -g -R ~/rpmbuild/SPECS/openwebstart.spec   # downloads the .deb

# Build
rpmbuild -bb ~/rpmbuild/SPECS/openwebstart.spec
sudo dnf install ~/rpmbuild/RPMS/x86_64/openwebstart-*.rpm
```

## Updates

When Karakun publishes a new release at
[karakun/OpenWebStart/releases](https://github.com/karakun/OpenWebStart/releases):

1. Bump `Version:` and `%global deb_underscored` in `openwebstart.spec`.
2. Add a `%changelog` entry.
3. Open a PR; once merged, COPR rebuilds against the new upstream `.deb`
   automatically (a webhook triggers the rebuild on push to `master`).

## License

The packaging files in this repository (the spec file, wrapper script,
desktop entries, MIME XML, and README) are released under
**GPL-2.0-only WITH Classpath-exception-2.0**, matching the upstream
OpenWebStart project's license. The upstream OpenWebStart binaries and
the bundled Adoptium Temurin JRE retain their original GPL-2.0 +
Classpath Exception terms; license texts are bundled inside the package
under `/opt/OpenWebStart/jre/LICENSE` and equivalent locations.
