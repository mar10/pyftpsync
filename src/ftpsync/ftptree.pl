# ftptree.pl
# dec 2001; martin@wwWendt.de
#
# todo:
#   - timing
use Carp;
use Getopt::Long;
use Net::FTP;

print "$0 12.2001 martin\@wwWendt.de ('-h' for help)\n";
die "\n" unless @ARGV;

# --- parse command line -----------------------------
Getopt::Long::Configure("no_ignore_case");

$Options = {};
Getopt::Long::GetOptions( $Options,
    'd=s',          # start directory (default: /)
    'h',            # help
    'k',            # print size in kbytes
    'pw:s',         # password
    't',            # tree only
    'v:i',          # Verbosity level
);
$Options->{v} += 0;
helpAndExit() if $Options->{h}; #$Options->{h}; # And exit

$hostname = shift @ARGV;
$username = shift @ARGV || 'anonymous';
$password = $Options->{pw};
if ( $password eq '' && $username ne 'anonymous' ) {
  print "Enter password for '$username': ";
  $password = readline STDIN;
  chomp ($password);
}
$homedir  = $Options->{d};
$treeOnly = $Options->{t};
$showKb   = $Options->{k};
$debug    = $Options->{v};

helpAndExit() if $hostname eq '';

$startTime = time;

# --- connect --------------------------------
print ("connecting '$hostname'... ");
my $ftp = Net::FTP->new ($hostname) || die "failed ($!)\n";

print ("login as '$username'... ");
$ftp->login ($username, $password) || die "failed ($!)\n";
if ( $homedir ne '' ) {
  print ("cwd '$homedir'... ");
  $ftp->cwd ($homedir) || die "failed ($!)\n";
}
print "ok.\n";


# --- read directories recursively ----------------
my %hresult = (); # this global hash stores the result list: <dirpath> => <info string>

my ($totalBytes, $totalFiles, $totalDirs) = scanSubDir();

$ftp->quit() || die "error closing connection ($!)\n";

# --- sort result list alphabetically
@asorted = sort { uc($a)cmp uc($b); } keys %hresult;

# --- convert path list into tree
@atree = makeTreeFromPathlist ($hostname.'/', 30, \@asorted);

print "\n                                                                 \n";
for ($i=0; $i<@asorted; $i++) {
  print "$atree[$i]";
  print ": $hresult{$asorted[$i]}" unless $treeOnly;
  print "\n";
}

print "\nTOTAL of " . getByteString($totalBytes) . "Bytes in $totalFiles files in $totalDirs dirs.\n";
#($sec,$min,$hour) = localtime(time-$startTime);
#print "elap: $min:$sec\n";

################################################################################
# scanSubDir()
# Recursively scans current remote directory
# returns ($branchBytes, $branchFiles, $branchDirs)
sub scanSubDir {
  local $line;
  local $dirBytes = 0;
  local $dirFiles = 0;
  local $branchBytes = 0;
  local $branchFiles = 0;
  local $branchDirs  = 0;
  local $cd = $ftp->pwd();

  tickDir ($cd);

  local $radir = $ftp->dir() || die "failed ($!)\n";

  sort @$radir;

  $branchDirs ++;
  
  foreach $line (@$radir) {
    print "$line\n" if $debug>2;

    # split directory entry into parts
    ($flags, $x, $user, $group, $size, $mon, $day, $timeOrYear, $fname) = split m/\s+/g, $line;

    if ( $fname eq '..' || $fname eq '.' || $fname eq '' ) {
      # skip current and up-dir entry

    } elsif ( substr($flags,0,1) eq 'd' ) {
      # recurse into directories
      $ftp->cwd ($fname) || die "error changing remote path to $fname ($!)\n";
      local ($bb, $bf, $bd) = scanSubDir();
      $ftp->cdup() || die "error changing remote path to .. ($!)\n";
      $branchBytes += $bb;
      $branchFiles += $bf;
      $branchDirs  += $bd;

    } else {
      # simple file: update statistics
      $dirBytes += $size;
      $dirFiles++;
      $branchBytes += $size;
      $branchFiles++;
    }
  }
  local $res = getByteString($dirBytes) . "Bytes in $dirFiles files";
  if ( $dirBytes!=$branchBytes ) {
    $res = $res . " (total: " . getByteString($branchBytes) . "/$branchFiles)";
  }
  # add to result hash
  $hresult{$cd} = $res;
  # return ersult vector
  return ($branchBytes, $branchFiles, $branchDirs);
} # end: scanSubDir

################################################################################
# tickDir()
sub tickDir {
  $nDirs ++;
#  print "reading ($nDirs directories)...                                    \r";
  print "reading $nDirs (@_)...                                    \r";
}

################################################################################
# getByteString ($bytes)
sub getByteString {
  carp 'usage: getByteString ($bytes)' unless @_==1;
  local ($bytes) = @_;
  $bytes = int($bytes / 1024 + .5) if $showKb;
	1 while $bytes =~ s/^([-+]?\d+)(\d{3})/$1,$2/; # insert thousands separator
  return $bytes . ($showKb?' k':' ');
}

################################################################################
# helpAndExit()
sub helpAndExit {
  { no warnings;
#      exec "pod2usage $0";
       exec "perldoc $0";
       exec "pod2text $0";
  }
}

################################################################################
# makeTreeFromPathlist ($prefix, $minwidth, \@array)
# returns array of tree prefixes
sub makeTreeFromPathlist {
  carp 'usage: makeTreeFromPathlist ($prefix,$minwidth,\@array)' unless @_==3;
  local ($prefix, $minwidth, $ra) = @_;

  local $PREFIX_EMPTY = '   ';
  local $PREFIX_PIPE  = ' | ';
  local $PREFIX_PLUS  = ' +-';

  # convert into a grid (one entry per line, containing a reference to @arow
  local @agrid;
  local $maxCols;
  foreach (@$ra) {
    local @arow = split m/\\|\/+/g;
    unshift @arow, $prefix if $prefix ne '';
    push @agrid, \@arow;
    $maxCols = @arow if @arow>$maxCols;
  }
#  print $maxCols . " x " . @agrid . "\n";
  printGrid (\@agrid) if $debug>2;

  # Spaltenweise von oben nach unten:
  # alle doppelten Namen durch '' ersetzen
  for ($x=0; $x<$maxCols; $x++) {
    local $prev = getGridAt (\@agrid,$x,0);
    for ($y=1; $y<@agrid; $y++) {
      local $item = getGridAt (\@agrid,$x,$y);
#     print "item [$x,$y] = '$item' ($prev)\n";
      setGridAt (\@agrid,$x,$y,$PREFIX_EMPTY) if uc($item) eq uc($prev);
      $prev = $item
    }
  }
  printGrid (\@agrid) if $debug>2;

  # Zeilenweise von rechts nach links:
  # alle ' ', die links vor einem Eintrag stehen durch '+-' ersetzen
  for ($y=0; $y<@agrid; $y++) {
    for ($x=0; $x<$maxCols; $x++) {
      local $item = getGridAt (\@agrid,$x,$y);
  #   print "item [$x,$y] = '$item'\n";
      if ( $item ne $PREFIX_EMPTY ) {
        setGridAt (\@agrid,$x-1,$y,$PREFIX_PLUS) if $x>0;
        last;
      }
    }
  }
  printGrid (\@agrid) if $debug>2;

  # Spaltenweise von unten nach oben:
  # alle ' ' oberhalb von '+-' durch '|' ersetzen
  for ($x=0; $x<$maxCols; $x++) {
    local $pipeMode = 0;
    for ($y=@agrid-1; $y>0; $y--) {
      local $item = getGridAt (\@agrid,$x,$y);
  #   print "item [$x,$y] = '$item', mode = $pipeMode\n";
      setGridAt (\@agrid,$x,$y,$PREFIX_PIPE) if $pipeMode && $item eq $PREFIX_EMPTY;
      $pipeMode = 1 if $item eq $PREFIX_PLUS;
      $pipeMode = 0 if $item ne $PREFIX_PLUS && $item ne $PREFIX_EMPTY;
    }
  }
  printGrid (\@agrid) if $debug>2;

  # convert rows to strings
  my @res;
  for ($y=0; $y<@agrid; $y++) {
    local $item = '';
    for ($x=0; $x<$maxCols; $x++) {
      $item = $item . getGridAt (\@agrid,$x,$y);
    }
    $item =~ s/\s*$//g; # trim
    $item = $item . ' ' x ($minwidth-length($item)) if length($item)<$minwidth;
    push @res, $item;
  }
  return @res;
}

################################################################################
# grid functions
sub getGridAt {
  carp 'usage: getGridAt (\@array,$x,$y)' unless @_==3;
  local ($ra, $x, $y) = @_;
  local $rarow = $agrid[$y];
  return @$rarow[$x];
}
sub setGridAt {
  carp 'usage: setGridAt (\@array,$x,$y,$value)' unless @_==4;
  local ($ra, $x, $y,$v) = @_;
  local $rarow = $agrid[$y];
  @$rarow[$x] = $v;
}
sub printGrid {
  local $parm = @_[0];
  local @ag = @$parm;
  local $x;
  foreach (@ag) {
    local @arow = @$_;
    print ++$x . " @arow \n";
  }
}

################################################################################
# Documentation
__END__

=head1 NAME

F<ftptree> - reads directory tree information from FTP host.

=head1 SYNOPSIS

 $ ftptree [OPTIONS] hostname [username]
    
 $ ftptree myhost                     # connect to ftp://myhost/ as 'anonymous'
 $ ftptree -d=pub -k -pw=foo myhost myname


=head1 DESCRIPTION

F<ftptree> recursively reads the directory structure of a FTP server.
...
...

=head1 OPTIONS

=over 4

=item -pwI<password>

Specifies the password.

=item -dI<directory>

Specifies the top level directory (default: /).

=item -h

Display this help.

=item -k

Show statistics in kBytes.

=item -t

Show tree only (without statistics).

=item -v

Increase verbosity of output; can be repeated for more verbose output.

=back

=cut

__END__
