# Binary repack of upstream OpenWebStart .deb. The package ships its own
# bundled Adoptium JRE 8 under %{oo_path}/jre, so the host's Java version
# (or absence thereof) is irrelevant.
#
# A small wrapper around the upstream `javaws` binary (Source4) injects
# -Dhttp.keepAlive=false into the JNLP runtime's command line, working
# around an iDRAC 7/8 HTTPS keep-alive bug that otherwise prevents
# OpenWebStart from downloading the main viewer jar.

%global oo_path /opt/OpenWebStart
%global deb_underscored 1_14_0

# Skip RPM's default build-post processing for binary repacks: no debug
# extraction, no strip (binaries are already stripped by upstream), no
# build-id links (these are install4j-built executables without our debuginfo).
%global debug_package %{nil}
%global __strip /bin/true
%global _build_id_links none
# Don't auto-derive Requires from bundled binaries: the bundled JRE links
# to standard glibc-stack libs already present on every Fedora system.
AutoReqProv: no

Name:           openwebstart
Version:        1.14.0
Release:        1%{?dist}
Summary:        Java Web Start replacement that opens .jnlp files

License:        GPL-2.0-only WITH Classpath-exception-2.0
URL:            https://openwebstart.com
Source0:        https://github.com/karakun/OpenWebStart/releases/download/v%{version}/OpenWebStart_linux_%{deb_underscored}.deb
Source1:        openwebstart.desktop
Source2:        openwebstart-settings.desktop
Source3:        openwebstart.xml
Source4:        javaws-keepalive-wrapper.sh

ExclusiveArch:  x86_64
BuildRequires:  binutils
BuildRequires:  tar

Requires:       glibc
Requires:       desktop-file-utils
Requires:       shared-mime-info

# icedtea-web ships /usr/bin/javaws too; only one javaws per system.
Conflicts:      icedtea-web

Provides:       javaws

%description
OpenWebStart is an open-source replacement for Oracle Java Web Start, which
was removed from the JDK in version 11. It opens .jnlp files and supports
deployment.properties, signed-jar handling, proxy configuration, and per-app
JRE selection. A bundled Adoptium Temurin 8 JRE is shipped, so OpenWebStart
operates independently of the system Java.

This package is a binary repack of the upstream .deb release at
https://github.com/karakun/OpenWebStart, with a small wrapper around the
javaws launcher that works around an iDRAC 7/8 HTTPS keep-alive bug.

%prep
# Nothing to do — extraction happens in %install.

%install
mkdir -p %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/mime/packages

# Extract upstream .deb's data tarball directly into the buildroot.
# `ar p` writes the named member to stdout; tar reads it and lays out
# /opt/OpenWebStart/* underneath %{buildroot}.
ar p %{SOURCE0} data.tar.gz | tar -xz -C %{buildroot}

# Drop install4j's leftover desktop file template inside the install dir;
# we ship a proper one under /usr/share/applications instead.
rm -f %{buildroot}%{oo_path}/.install4j/install4j_*-itw-settings.desktop

# Move the real javaws aside and install our keep-alive wrapper in its
# place. The desktop entry's Exec= and the /usr/bin/javaws symlink keep
# pointing at %{oo_path}/javaws, which is now the wrapper.
mv %{buildroot}%{oo_path}/javaws %{buildroot}%{oo_path}/javaws.real
install -m 0755 %{SOURCE4} %{buildroot}%{oo_path}/javaws

# Launchers on PATH.
ln -s %{oo_path}/javaws        %{buildroot}%{_bindir}/javaws
ln -s %{oo_path}/itw-settings  %{buildroot}%{_bindir}/itw-settings

# Desktop entries and MIME registration.
install -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/openwebstart.desktop
install -m 0644 %{SOURCE2} %{buildroot}%{_datadir}/applications/openwebstart-settings.desktop
install -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/mime/packages/openwebstart.xml

%post
update-mime-database     %{_datadir}/mime         &>/dev/null || :
update-desktop-database  %{_datadir}/applications &>/dev/null || :

%postun
update-mime-database     %{_datadir}/mime         &>/dev/null || :
update-desktop-database  %{_datadir}/applications &>/dev/null || :

%files
%{oo_path}
%{_bindir}/javaws
%{_bindir}/itw-settings
%{_datadir}/applications/openwebstart.desktop
%{_datadir}/applications/openwebstart-settings.desktop
%{_datadir}/mime/packages/openwebstart.xml

%changelog
* Mon Jul 06 2026 Zoltan Szepesi <2dcube01@gmail.com> - 1.14.0-1
- Update to upstream OpenWebStart 1.14.0

* Wed Apr 29 2026 Zoltan Szepesi <2dcube01@gmail.com> - 1.13.0-2
- Add javaws wrapper that injects -Dhttp.keepAlive=false to work around
  a Dell iDRAC 7/8 HTTPS keep-alive bug which otherwise prevents the
  KVM viewer jar from downloading.

* Tue Apr 28 2026 Zoltan Szepesi <2dcube01@gmail.com> - 1.13.0-1
- Initial binary repack of upstream OpenWebStart 1.13.0 .deb
