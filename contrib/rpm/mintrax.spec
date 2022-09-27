%define bdbv 4.8.30
%global selinux_variants mls strict targeted

%if 0%{?_no_gui:1}
%define _buildqt 0
%define buildargs --with-gui=no
%else
%define _buildqt 1
%if 0%{?_use_qt4}
%define buildargs --with-qrencode --with-gui=qt4
%else
%define buildargs --with-qrencode --with-gui=qt5
%endif
%endif

Name:		mintrax
Version:	0.12.0
Release:	2%{?dist}
Summary:	Peer to Peer Cryptographic Currency

Group:		Applications/System
License:	MIT
URL:		https://mintrax.org/
Source0:	https://mintrax.org/bin/mintrax-core-%{version}/mintrax-%{version}.tar.gz
Source1:	http://download.oracle.com/berkeley-db/db-%{bdbv}.NC.tar.gz

Source10:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/contrib/debian/examples/mintrax.conf

#man pages
Source20:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/doc/man/mintraxd.1
Source21:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/doc/man/mintrax-cli.1
Source22:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/doc/man/mintrax-qt.1

#selinux
Source30:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/contrib/rpm/mintrax.te
# Source31 - what about mintrax-tx and bench_mintrax ???
Source31:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/contrib/rpm/mintrax.fc
Source32:	https://raw.githubusercontent.com/mintrax910/mintrax/v%{version}/contrib/rpm/mintrax.if

Source100:	https://upload.wikimedia.org/wikipedia/commons/4/46/Bitcoin.svg

%if 0%{?_use_libressl:1}
BuildRequires:	libressl-devel
%else
BuildRequires:	openssl-devel
%endif
BuildRequires:	boost-devel
BuildRequires:	miniupnpc-devel
BuildRequires:	autoconf automake libtool
BuildRequires:	libevent-devel


Patch0:		mintrax-0.12.0-libressl.patch


%description
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of mintraxs is carried out collectively by the network.

%if %{_buildqt}
%package core
Summary:	Peer to Peer Cryptographic Currency
Group:		Applications/System
Obsoletes:	%{name} < %{version}-%{release}
Provides:	%{name} = %{version}-%{release}
%if 0%{?_use_qt4}
BuildRequires:	qt-devel
%else
BuildRequires:	qt5-qtbase-devel
# for /usr/bin/lrelease-qt5
BuildRequires:	qt5-linguist
%endif
BuildRequires:	protobuf-devel
BuildRequires:	qrencode-devel
BuildRequires:	%{_bindir}/desktop-file-validate
# for icon generation from SVG
BuildRequires:	%{_bindir}/inkscape
BuildRequires:	%{_bindir}/convert

%description core
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of mintraxs is carried out collectively by the network.

This package contains the Qt based graphical client and node. If you are looking
to run a Bitcoin wallet, this is probably the package you want.
%endif


%package libs
Summary:	Bitcoin shared libraries
Group:		System Environment/Libraries

%description libs
This package provides the mintraxconsensus shared libraries. These libraries
may be used by third party software to provide consensus verification
functionality.

Unless you know need this package, you probably do not.

%package devel
Summary:	Development files for mintrax
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description devel
This package contains the header files and static library for the
mintraxconsensus shared library. If you are developing or compiling software
that wants to link against that library, then you need this package installed.

Most people do not need this package installed.

%package server
Summary:	The mintrax daemon
Group:		System Environment/Daemons
Requires:	mintrax-utils = %{version}-%{release}
Requires:	selinux-policy policycoreutils-python
Requires(pre):	shadow-utils
Requires(post):	%{_sbindir}/semodule %{_sbindir}/restorecon %{_sbindir}/fixfiles %{_sbindir}/sestatus
Requires(postun):	%{_sbindir}/semodule %{_sbindir}/restorecon %{_sbindir}/fixfiles %{_sbindir}/sestatus
BuildRequires:	systemd
BuildRequires:	checkpolicy
BuildRequires:	%{_datadir}/selinux/devel/Makefile

%description server
This package provides a stand-alone mintrax-core daemon. For most users, this
package is only needed if they need a full-node without the graphical client.

Some third party wallet software will want this package to provide the actual
mintrax-core node they use to connect to the network.

If you use the graphical mintrax-core client then you almost certainly do not
need this package.

%package utils
Summary:	Bitcoin utilities
Group:		Applications/System

%description utils
This package provides several command line utilities for interacting with a
mintrax-core daemon.

The mintrax-cli utility allows you to communicate and control a mintrax daemon
over RPC, the mintrax-tx utility allows you to create a custom transaction, and
the bench_mintrax utility can be used to perform some benchmarks.

This package contains utilities needed by the mintrax-server package.


%prep
%setup -q
%patch0 -p1 -b .libressl
cp -p %{SOURCE10} ./mintrax.conf.example
tar -zxf %{SOURCE1}
cp -p db-%{bdbv}.NC/LICENSE ./db-%{bdbv}.NC-LICENSE
mkdir db4 SELinux
cp -p %{SOURCE30} %{SOURCE31} %{SOURCE32} SELinux/


%build
CWD=`pwd`
cd db-%{bdbv}.NC/build_unix/
../dist/configure --enable-cxx --disable-shared --with-pic --prefix=${CWD}/db4
make install
cd ../..

./autogen.sh
%configure LDFLAGS="-L${CWD}/db4/lib/" CPPFLAGS="-I${CWD}/db4/include/" --with-miniupnpc --enable-glibc-back-compat %{buildargs}
make %{?_smp_mflags}

pushd SELinux
for selinuxvariant in %{selinux_variants}; do
	make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
	mv mintrax.pp mintrax.pp.${selinuxvariant}
	make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done
popd


%install
make install DESTDIR=%{buildroot}

mkdir -p -m755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/mintraxd %{buildroot}%{_sbindir}/mintraxd

# systemd stuff
mkdir -p %{buildroot}%{_tmpfilesdir}
cat <<EOF > %{buildroot}%{_tmpfilesdir}/mintrax.conf
d /run/mintraxd 0750 mintrax mintrax -
EOF
touch -a -m -t 201504280000 %{buildroot}%{_tmpfilesdir}/mintrax.conf

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
cat <<EOF > %{buildroot}%{_sysconfdir}/sysconfig/mintrax
# Provide options to the mintrax daemon here, for example
# OPTIONS="-testnet -disable-wallet"

OPTIONS=""

# System service defaults.
# Don't change these unless you know what you're doing.
CONFIG_FILE="%{_sysconfdir}/mintrax/mintrax.conf"
DATA_DIR="%{_localstatedir}/lib/mintrax"
PID_FILE="/run/mintraxd/mintraxd.pid"
EOF
touch -a -m -t 201504280000 %{buildroot}%{_sysconfdir}/sysconfig/mintrax

mkdir -p %{buildroot}%{_unitdir}
cat <<EOF > %{buildroot}%{_unitdir}/mintrax.service
[Unit]
Description=Bitcoin daemon
After=syslog.target network.target

[Service]
Type=forking
ExecStart=%{_sbindir}/mintraxd -daemon -conf=\${CONFIG_FILE} -datadir=\${DATA_DIR} -pid=\${PID_FILE} \$OPTIONS
EnvironmentFile=%{_sysconfdir}/sysconfig/mintrax
User=mintrax
Group=mintrax

Restart=on-failure
PrivateTmp=true
TimeoutStopSec=120
TimeoutStartSec=60
StartLimitInterval=240
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
EOF
touch -a -m -t 201504280000 %{buildroot}%{_unitdir}/mintrax.service
#end systemd stuff

mkdir %{buildroot}%{_sysconfdir}/mintrax
mkdir -p %{buildroot}%{_localstatedir}/lib/mintrax

#SELinux
for selinuxvariant in %{selinux_variants}; do
	install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
	install -p -m 644 SELinux/mintrax.pp.${selinuxvariant} %{buildroot}%{_datadir}/selinux/${selinuxvariant}/mintrax.pp
done

%if %{_buildqt}
# qt icons
install -D -p share/pixmaps/mintrax.ico %{buildroot}%{_datadir}/pixmaps/mintrax.ico
install -p share/pixmaps/nsis-header.bmp %{buildroot}%{_datadir}/pixmaps/
install -p share/pixmaps/nsis-wizard.bmp %{buildroot}%{_datadir}/pixmaps/
install -p %{SOURCE100} %{buildroot}%{_datadir}/pixmaps/mintrax.svg
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/mintrax16.png -w16 -h16
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/mintrax32.png -w32 -h32
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/mintrax64.png -w64 -h64
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/mintrax128.png -w128 -h128
%{_bindir}/inkscape %{SOURCE100} --export-png=%{buildroot}%{_datadir}/pixmaps/mintrax256.png -w256 -h256
%{_bindir}/convert -resize 16x16 %{buildroot}%{_datadir}/pixmaps/mintrax256.png %{buildroot}%{_datadir}/pixmaps/mintrax16.xpm
%{_bindir}/convert -resize 32x32 %{buildroot}%{_datadir}/pixmaps/mintrax256.png %{buildroot}%{_datadir}/pixmaps/mintrax32.xpm
%{_bindir}/convert -resize 64x64 %{buildroot}%{_datadir}/pixmaps/mintrax256.png %{buildroot}%{_datadir}/pixmaps/mintrax64.xpm
%{_bindir}/convert -resize 128x128 %{buildroot}%{_datadir}/pixmaps/mintrax256.png %{buildroot}%{_datadir}/pixmaps/mintrax128.xpm
%{_bindir}/convert %{buildroot}%{_datadir}/pixmaps/mintrax256.png %{buildroot}%{_datadir}/pixmaps/mintrax256.xpm
touch %{buildroot}%{_datadir}/pixmaps/*.png -r %{SOURCE100}
touch %{buildroot}%{_datadir}/pixmaps/*.xpm -r %{SOURCE100}

# Desktop File - change the touch timestamp if modifying
mkdir -p %{buildroot}%{_datadir}/applications
cat <<EOF > %{buildroot}%{_datadir}/applications/mintrax-core.desktop
[Desktop Entry]
Encoding=UTF-8
Name=Bitcoin
Comment=Bitcoin P2P Cryptocurrency
Comment[fr]=Bitcoin, monnaie virtuelle cryptographique pair à pair
Comment[tr]=Bitcoin, eşten eşe kriptografik sanal para birimi
Exec=mintrax-qt %u
Terminal=false
Type=Application
Icon=mintrax128
MimeType=x-scheme-handler/mintrax;
Categories=Office;Finance;
EOF
# change touch date when modifying desktop
touch -a -m -t 201511100546 %{buildroot}%{_datadir}/applications/mintrax-core.desktop
%{_bindir}/desktop-file-validate %{buildroot}%{_datadir}/applications/mintrax-core.desktop

# KDE protocol - change the touch timestamp if modifying
mkdir -p %{buildroot}%{_datadir}/kde4/services
cat <<EOF > %{buildroot}%{_datadir}/kde4/services/mintrax-core.protocol
[Protocol]
exec=mintrax-qt '%u'
protocol=mintrax
input=none
output=none
helper=true
listing=
reading=false
writing=false
makedir=false
deleting=false
EOF
# change touch date when modifying protocol
touch -a -m -t 201511100546 %{buildroot}%{_datadir}/kde4/services/mintrax-core.protocol
%endif

# man pages
install -D -p %{SOURCE20} %{buildroot}%{_mandir}/man1/mintraxd.1
install -p %{SOURCE21} %{buildroot}%{_mandir}/man1/mintrax-cli.1
%if %{_buildqt}
install -p %{SOURCE22} %{buildroot}%{_mandir}/man1/mintrax-qt.1
%endif

# nuke these, we do extensive testing of binaries in %%check before packaging
rm -f %{buildroot}%{_bindir}/test_*

%check
make check
srcdir=src test/mintrax-util-test.py
test/functional/test_runner.py --extended

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%pre server
getent group mintrax >/dev/null || groupadd -r mintrax
getent passwd mintrax >/dev/null ||
	useradd -r -g mintrax -d /var/lib/mintrax -s /sbin/nologin \
	-c "Bitcoin wallet server" mintrax
exit 0

%post server
%systemd_post mintrax.service
# SELinux
if [ `%{_sbindir}/sestatus |grep -c "disabled"` -eq 0 ]; then
for selinuxvariant in %{selinux_variants}; do
	%{_sbindir}/semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/mintrax.pp &> /dev/null || :
done
%{_sbindir}/semanage port -a -t mintrax_port_t -p tcp 8332
%{_sbindir}/semanage port -a -t mintrax_port_t -p tcp 8333
%{_sbindir}/semanage port -a -t mintrax_port_t -p tcp 18332
%{_sbindir}/semanage port -a -t mintrax_port_t -p tcp 18333
%{_sbindir}/semanage port -a -t mintrax_port_t -p tcp 18443
%{_sbindir}/semanage port -a -t mintrax_port_t -p tcp 18444
%{_sbindir}/fixfiles -R mintrax-server restore &> /dev/null || :
%{_sbindir}/restorecon -R %{_localstatedir}/lib/mintrax || :
fi

%posttrans server
%{_bindir}/systemd-tmpfiles --create

%preun server
%systemd_preun mintrax.service

%postun server
%systemd_postun mintrax.service
# SELinux
if [ $1 -eq 0 ]; then
	if [ `%{_sbindir}/sestatus |grep -c "disabled"` -eq 0 ]; then
	%{_sbindir}/semanage port -d -p tcp 8332
	%{_sbindir}/semanage port -d -p tcp 8333
	%{_sbindir}/semanage port -d -p tcp 18332
	%{_sbindir}/semanage port -d -p tcp 18333
	%{_sbindir}/semanage port -d -p tcp 18443
	%{_sbindir}/semanage port -d -p tcp 18444
	for selinuxvariant in %{selinux_variants}; do
		%{_sbindir}/semodule -s ${selinuxvariant} -r mintrax &> /dev/null || :
	done
	%{_sbindir}/fixfiles -R mintrax-server restore &> /dev/null || :
	[ -d %{_localstatedir}/lib/mintrax ] && \
		%{_sbindir}/restorecon -R %{_localstatedir}/lib/mintrax &> /dev/null || :
	fi
fi

%clean
rm -rf %{buildroot}

%if %{_buildqt}
%files core
%defattr(-,root,root,-)
%license COPYING db-%{bdbv}.NC-LICENSE
%doc COPYING mintrax.conf.example doc/README.md doc/bips.md doc/files.md doc/multiwallet-qt.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md
%attr(0755,root,root) %{_bindir}/mintrax-qt
%attr(0644,root,root) %{_datadir}/applications/mintrax-core.desktop
%attr(0644,root,root) %{_datadir}/kde4/services/mintrax-core.protocol
%attr(0644,root,root) %{_datadir}/pixmaps/*.ico
%attr(0644,root,root) %{_datadir}/pixmaps/*.bmp
%attr(0644,root,root) %{_datadir}/pixmaps/*.svg
%attr(0644,root,root) %{_datadir}/pixmaps/*.png
%attr(0644,root,root) %{_datadir}/pixmaps/*.xpm
%attr(0644,root,root) %{_mandir}/man1/mintrax-qt.1*
%endif

%files libs
%defattr(-,root,root,-)
%license COPYING
%doc COPYING doc/README.md doc/shared-libraries.md
%{_libdir}/lib*.so.*

%files devel
%defattr(-,root,root,-)
%license COPYING
%doc COPYING doc/README.md doc/developer-notes.md doc/shared-libraries.md
%attr(0644,root,root) %{_includedir}/*.h
%{_libdir}/*.so
%{_libdir}/*.a
%{_libdir}/*.la
%attr(0644,root,root) %{_libdir}/pkgconfig/*.pc

%files server
%defattr(-,root,root,-)
%license COPYING db-%{bdbv}.NC-LICENSE
%doc COPYING mintrax.conf.example doc/README.md doc/REST-interface.md doc/bips.md doc/dnsseed-policy.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md
%attr(0755,root,root) %{_sbindir}/mintraxd
%attr(0644,root,root) %{_tmpfilesdir}/mintrax.conf
%attr(0644,root,root) %{_unitdir}/mintrax.service
%dir %attr(0750,mintrax,mintrax) %{_sysconfdir}/mintrax
%dir %attr(0750,mintrax,mintrax) %{_localstatedir}/lib/mintrax
%config(noreplace) %attr(0600,root,root) %{_sysconfdir}/sysconfig/mintrax
%attr(0644,root,root) %{_datadir}/selinux/*/*.pp
%attr(0644,root,root) %{_mandir}/man1/mintraxd.1*

%files utils
%defattr(-,root,root,-)
%license COPYING
%doc COPYING mintrax.conf.example doc/README.md
%attr(0755,root,root) %{_bindir}/mintrax-cli
%attr(0755,root,root) %{_bindir}/mintrax-tx
%attr(0755,root,root) %{_bindir}/bench_mintrax
%attr(0644,root,root) %{_mandir}/man1/mintrax-cli.1*



%changelog
* Fri Feb 26 2016 Alice Wonder <buildmaster@librelamp.com> - 0.12.0-2
- Rename Qt package from mintrax to mintrax-core
- Make building of the Qt package optional
- When building the Qt package, default to Qt5 but allow building
-  against Qt4
- Only run SELinux stuff in post scripts if it is not set to disabled

* Wed Feb 24 2016 Alice Wonder <buildmaster@librelamp.com> - 0.12.0-1
- Initial spec file for 0.12.0 release

# This spec file is written from scratch but a lot of the packaging decisions are directly
# based upon the 0.11.2 package spec file from https://www.ringingliberty.com/mintrax/
