#!/usr/bin/env perl
#
use strict; 
use Fcntl; 
use DB_File;
my %f = undef;

my $status = 1;
my ($node, $flag_new) = @ARGV;  

my $dir_local = "."; 
my $dir_remote = "/usr/share/pyshared/sardana/sardana-macros/DESY_general"; 

my ($dev, $ino, $mode, $nlink, $uid, $gid, 
    $rdev, $size, $atime, $mtime, $ctime, $blksize, $blocks);

if(  !defined( $node))
{
    print "\n Usage: ./Update_files.pl <node> <new> \n\n";
    $status = 0;
    goto finish;
}
if( ! -e "${dir_local}/Files.lis")
{
    print " Error: Files.lis is missing \n";
    $status = 0;
    goto finish;
}

my @files = `cat ${dir_local}/Files.lis`;
@files = grep !/^#/, @files;

my $filename = "${dir_local}/Files.db";
my $flagTie = 1;
if( !(tie %f, "DB_File", "$filename", O_RDWR, 0777, $DB_HASH))
{
    $flagTie = 0;
    if( !(tie %f, "DB_File", "$filename", O_CREAT, 0777, $DB_HASH))
    {
        print " Error: failed to open $filename \n";
        $status = 0;
        goto finish;
    }
}
#
# see, if the target directory exists on the remote host
#
my $ret = `ssh root\@$node "test -d $dir_remote || echo notexist"`;
if( $ret =~ /notexist/)
{
    print " $dir_remote does not exist on $node \n"; 
    $status = 0;
    goto finish;
}

my $flag_upToDate = 1; 
foreach my $file (@files)
{
    $file =~ s/^\s*(.*?)\s*$/$1/;   
    if( length( $file) == 0)
    {
        next;
    }
    if( ! -e "${dir_local}/${file}")
    {
        print " Error: ${dir_local}/${file} is missing \n";
        $status = 0;
        goto finish;
    }
    ($dev, $ino, $mode, $nlink, $uid, $gid, 
     $rdev, $size, $atime, $mtime, $ctime, $blksize, $blocks) = 
         stat "${dir_local}/${file}";
    
    if( (defined $f{ "${node}_${file}_mtime"}) &&
        ($mtime <= $f{ "${node}_${file}_mtime"}) &&
        ($flag_new !~ /new/i))
    {	
        next;
    }

    $flag_upToDate = 0;
    print " copying ${dir_local}/${file} to ${node}:${dir_remote} \n";
    $status = !system( "scp ${dir_local}/${file} root\@${node}:${dir_remote} >/dev/null");
    if( !$status)
    {
        goto finish;
    }
    $f{ "${node}_${file}_mtime"} =  $mtime;
}

 finish:

if( $flagTie)
{
    untie %f;
}

if( $flag_upToDate)
{
    print " --- scripts/Update_files.pl: all files are up-to-date on $node\n"; 
}
else
{
    print " --- scripts/Update_files.pl: done on $node, status $status \n"; 
}

!$status;

