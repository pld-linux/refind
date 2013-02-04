# TODO
# - add efi-boot-update pld script support
# - review inlined scriptlets
Summary:	EFI boot manager software
Name:		refind
Version:	0.6.6
Release:	0.1
License:	GPL v3
Group:		Base
URL:		http://www.rodsbooks.com/refind/
Source0:	http://downloads.sourceforge.net/refind/%{name}-src-%{version}.zip
# Source0-md5:	ca357e43c0cca4a56ec60a2827514a0d
BuildRequires:	gnu-efi
BuildRequires:	unzip
Requires:	efibootmgr
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define efiarch unknown
%ifarch i386
%define efiarch ia32
%endif
%ifarch i486
%define efiarch ia32
%endif
%ifarch i586
%define efiarch ia32
%endif
%ifarch i686
%define efiarch ia32
%endif
%ifarch x86_64
%define efiarch x64
%endif

# Directory in which refind.key and refind.crt files are found for
# signing of binaries. If absent, binaries are copied unsigned.
%define keydir /mnt/refind

%description
A graphical boot manager for EFI- and UEFI-based computers, such as
all Intel-based Macs and recent (most 2011 and later) PCs. rEFInd
presents a boot menu showing all the EFI boot loaders on the
EFI-accessible partitions, and optionally BIOS-bootable partitions on
Macs. EFI-compatbile OSes, including Linux, provide boot loaders that
rEFInd can detect and launch. rEFInd can launch Linux EFI boot loaders
such as ELILO, GRUB Legacy, GRUB 2, and 3.3.0 and later kernels with
EFI stub support. EFI filesystem drivers for ext2/3/4fs, ReiserFS,
HFS+, and ISO-9660 enable rEFInd to read boot loaders from these
filesystems, too. rEFInd's ability to detect boot loaders at runtime
makes it very easy to use, particularly when paired with Linux kernels
that provide EFI stub support.

%prep
%setup -q

%build
%{__make} gnuefi fs_gnuefi \
	CC="%{__cc}" \
	CXX="%{__cxx}" \
	CXXFLAGS="-fpic -D_REENTRANT -D_GNU_SOURCE -Wall %{rpmcxxflags}"

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind

# Copy the rEFInd binaries (rEFInd proper and drivers) to %{_datadir}/%{name}-%{version},
# including signing the binaries if sbsign is installed and a %{keydir}/refind.key file
# is available
SBSign=$(which sbsign 2> /dev/null || :)
if [ -f %{keydir}/refind.key -a -x $SBSign ] ; then
	$SBSign --key %{keydir}/refind.key --cert %{keydir}/refind.crt --output $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/refind_%{efiarch}.efi refind/refind_%{efiarch}.efi
	install -d $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/drivers_%{efiarch}
	for File in $(ls drivers_%{efiarch}/*_x64.efi); do
		$SBSign --key %{keydir}/refind.key --cert %{keydir}/refind.crt --output $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/$File $File
	done
else
	install -Dp refind/refind*.efi $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind
	install -d $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/drivers_%{efiarch}
	cp -a drivers_%{efiarch}/* $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/drivers_%{efiarch}
fi

# Copy configuration and support files to %{_datadir}/%{name}-%{version}
install -Dp refind.conf-sample $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/
cp -a icons $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/refind/
install -Dp install.sh $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}/

# Copy documentation to %{_docdir}/refind-%{version}
install -d $RPM_BUILD_ROOT%{_docdir}/refind-%{version}
cp -a docs/* $RPM_BUILD_ROOT%{_docdir}/refind-%{version}/
install -Dp NEWS.txt COPYING.txt LICENSE.txt README.txt CREDITS.txt $RPM_BUILD_ROOT%{_docdir}/refind-%{version}

# Copy keys to %{_sysconfdir}/refind.d/keys
install -d $RPM_BUILD_ROOT%{_sysconfdir}/refind.d/keys
install -Dp keys/* $RPM_BUILD_ROOT%{_sysconfdir}/refind.d/keys

# Copy scripts to %{_sbindir}
install -d $RPM_BUILD_ROOT%{_sbindir}
install -Dp mkrlconf.sh $RPM_BUILD_ROOT%{_sbindir}/
install -Dp mvrefind.sh $RPM_BUILD_ROOT%{_sbindir}/

# Copy banners and fonts to %{_datadir}/%{name}-%{version}
cp -a banners $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}
cp -a fonts $RPM_BUILD_ROOT%{_datadir}/%{name}-%{version}

%clean
rm -rf $RPM_BUILD_ROOT

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

%files
%defattr(644,root,root,755)
%doc %{_docdir}/refind-%{version}
%attr(755,root,root) %{_sbindir}/mkrlconf.sh
%attr(755,root,root) %{_sbindir}/mvrefind.sh
%{_datadir}/%{name}-%{version}
%dir %{_sysconfdir}/refind.d
%dir %{_sysconfdir}/refind.d/keys
%{_sysconfdir}/refind.d/keys/*
