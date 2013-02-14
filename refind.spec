# TODO
# - add efi-boot-update pld script support
# - review inlined scriptlets
# - note: invoking efibootmgr can cause firmware corruption on some mactel firmware
#   http://www.rodsbooks.com/refind/installing.html, but then you probably won't install this tool there
Summary:	EFI boot manager software
Summary(pl.UTF-8):	Boot manager dla platform EFI
Name:		refind
Version:	0.6.7
Release:	0.1
License:	GPL v3
Group:		Base
URL:		http://www.rodsbooks.com/refind/
Source0:	https://downloads.sourceforge.net/project/refind/%{version}/%{name}-src-%{version}.zip
# Source0-md5:	f118fd9fbc88f47b804746fbcbfb22e6
BuildRequires:	gnu-efi
BuildRequires:	unzip
Requires:	efibootmgr
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define efiarch unknown
%ifarch %{ix86}
%define efiarch ia32
%endif
%ifarch %{x8664}
%define efiarch x64
%endif

# Directory in which refind.key and refind.crt files are found for
# signing of binaries. If absent, binaries are copied unsigned.
%define		keydir	/mnt/refind

%description
A graphical boot manager for EFI- and UEFI-based computers, such as
all Intel-based Macs and recent (most 2011 and later) PCs. rEFInd
presents a boot menu showing all the EFI boot loaders on the
EFI-accessible partitions, and optionally BIOS-bootable partitions on
Macs. EFI-compatible OSes, including Linux, provide boot loaders that
rEFInd can detect and launch. rEFInd can launch Linux EFI boot loaders
such as ELILO, GRUB Legacy, GRUB 2, and 3.3.0 and later kernels with
EFI stub support. EFI filesystem drivers for ext2/3/4fs, ReiserFS,
HFS+, and ISO-9660 enable rEFInd to read boot loaders from these
filesystems, too. rEFInd's ability to detect boot loaders at runtime
makes it very easy to use, particularly when paired with Linux kernels
that provide EFI stub support.

%description -l pl.UTF-8
Graficzny boot manager dla komputerów opartych na EFI i UEFI, takich
jak wszystkie komputery Mac z procesorem Intela oraz nowsze PC
(większość wyprodukowanych od 2011 roku). rEFInd prezentuje menu
startowe pokazujące boot loadery EFI na partycjach dostępnych dla EFI
oraz opcjonalnie opartycje startowe BIOS-u na Makach. Systemy
operacyjne zgodne z EFI, w tym Linux, udostępniają boot loadery, które
rEFInd jest w stanie wykryć i uruchomić. rEFInd potrafi uruchomić
takie programy, jak ELILO, GRUB Legacy, GRUB 2 oraz jądra Linuksa w
wersji 3.3.0 lub nowszej z obsługą zaślepki EFI. Sterowniki EFI do
systemów plików ext2/3/4, ReiserFS, HFS+ oraz ISO-9660 umożliwiają
rEFIndowi uruchamianie programów także z tych systmów plików. rEFInd
potrafi wykrywać boot loadery w czasie działania, dzięki czemu jest
łatwy w użyciu, w szczególności w połączeniu z jądrami Linuksa z
obsługą zaślepki EFI.

%prep
%setup -q

%build
%{__make} gnuefi fs_gnuefi -j1 \
	CC="%{__cc}" \
	CXX="%{__cxx}" \
	CXXFLAGS="-fpic -D_REENTRANT -D_GNU_SOURCE -Wall %{rpmcxxflags}" \
	GNUEFILIB=%{_libdir} \
	EFILIB=%{_libdir} \
	EFICRT0=%{_libdir}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}

# Copy the rEFInd binaries (rEFInd proper and drivers) to %{_datadir}/%{name}-%{version},
# including signing the binaries if sbsign is installed and a %{keydir}/refind.key file
# is available
SBSign=$(which sbsign 2> /dev/null || :)
if [ -f %{keydir}/refind.key -a -x $SBSign ] ; then
	$SBSign --key %{keydir}/refind.key --cert %{keydir}/refind.crt --output $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}/refind_%{efiarch}.efi refind/refind_%{efiarch}.efi
	install -d $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}/drivers_%{efiarch}
	for File in $(ls drivers_%{efiarch}/*_x64.efi); do
		$SBSign --key %{keydir}/refind.key --cert %{keydir}/refind.crt --output $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}/$File $File
	done
else
	install -Dp refind/refind*.efi $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}
	install -d $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}/drivers_%{efiarch}
	cp -a drivers_%{efiarch}/* $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}/drivers_%{efiarch}
fi

# Copy configuration and support files to %{_datadir}/%{name}-%{version}
install -p refind.conf-sample $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}
cp -a icons $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/%{name}
install -p install.sh $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}

# Copy keys to %{_sysconfdir}/refind.d/keys
install -d $RPM_BUILD_ROOT%{_sysconfdir}/refind.d/keys
cp -a keys/* $RPM_BUILD_ROOT%{_sysconfdir}/refind.d/keys

# Copy scripts to %{_sbindir}
install -d $RPM_BUILD_ROOT%{_sbindir}
install -p mkrlconf.sh $RPM_BUILD_ROOT%{_sbindir}
install -p mvrefind.sh $RPM_BUILD_ROOT%{_sbindir}

# Copy banners and fonts to %{_datadir}/%{name}-%{version}
cp -a banners $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}
cp -a fonts $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}

%clean
rm -rf $RPM_BUILD_ROOT

%if 0
%post
PATH=$PATH:%{_prefix}/local/bin
# Remove any existing NVRAM entry for rEFInd, to avoid creating a duplicate.
ExistingEntry=$(efibootmgr | grep "rEFInd Boot Manager" | cut -c 5-8)
if [ -n $ExistingEntry ]; then
	efibootmgr --bootnum $ExistingEntry --delete-bootnum
fi

cd %{_datadir}/%{name}-%{version}

VarFile=$(ls -d /sys/firmware/efi/vars/SecureBoot* 2> /dev/null)
ShimFile=$(find /boot -name shim\.efi 2> /dev/null | head -n 1)
SBSign=$(which sbsign 2> /dev/null)
OpenSSL=$(which openssl 2> /dev/null)

# Run the rEFInd installation script. Do so with the --shim option
# if Secure Boot mode is suspected and if a shim program can be
# found, or without it if not. If a shim installation is attempted
# and the sbsign and openssl programs can be found, do the install
# using a local signing key. Note that this option is undesirable
# for a distribution, since it would then require the user to
# enroll an extra MOK. I'm including it here because I'm NOT a
# distribution maintainer, and I want to encourage users to use
# their own local keys.
if [ -n $VarFile -a -n $ShimFile ]; then
   if [ -n $SBSign -a -n $OpenSSL ]; then
	  ./install.sh --shim $ShimFile --localkeys --yes
   else
	  ./install.sh --shim $ShimFile --yes
   fi
else
	./install.sh --yes
fi

# CAUTION: Don't create a %preun or a %postun script that deletes the files
# installed by install.sh, since that script will run after an update, thus
# wiping out the just-updated files.
%endif

%files
%defattr(644,root,root,755)
%doc NEWS.txt LICENSE.txt README.txt CREDITS.txt docs/*
%dir %{_sysconfdir}/refind.d
%dir %{_sysconfdir}/refind.d/keys
%{_sysconfdir}/refind.d/keys/*
%attr(755,root,root) %{_sbindir}/mkrlconf.sh
%attr(755,root,root) %{_sbindir}/mvrefind.sh
%{_datadir}/%{name}-%{version}
