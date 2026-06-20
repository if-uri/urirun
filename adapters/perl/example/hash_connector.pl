# Reference urirun connector in Perl: prints a urirun.bindings.v2 document.
use strict;
use warnings;
use FindBin;
use lib "$FindBin::Bin/..";
use Urirun;

my $c = Urirun->new("hash", "hash");
$c->command(
    "sha256/command/file",
    { required => ["path"], properties => { path => { type => "string" } } },
    ["sha256sum", "{path}"],
);
print $c->bindings_json;
