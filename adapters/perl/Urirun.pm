# urirun — Perl SDK for building urirun.bindings.v2 documents.
package Urirun;
use strict;
use warnings;
use JSON::PP ();

our $BINDINGS_VERSION = "urirun.bindings.v2";

sub new {
    my ($class, $id, $scheme, $target) = @_;
    $target //= "host";
    return bless { id => $id, scheme => $scheme, target => $target, bindings => {} }, $class;
}

sub command {
    my ($self, $route, $schema, $argv) = @_;
    my $uri = "$self->{scheme}://$self->{target}/$route";
    my %input = (
        type                 => "object",
        additionalProperties => JSON::PP::false,
        properties           => ($schema->{properties} // {}),
    );
    $input{required} = $schema->{required}
        if $schema->{required} && @{ $schema->{required} };
    $self->{bindings}{$uri} = {
        uri         => $uri,
        kind        => "command",
        adapter     => "argv-template",
        inputSchema => \%input,
        argv        => $argv,
        meta        => { connector => $self->{id} },
        policy      => { allowExecute => JSON::PP::true },
    };
    return $self;
}

sub bindings {
    my $self = shift;
    return { version => $BINDINGS_VERSION, bindings => $self->{bindings} };
}

sub bindings_json {
    my $self = shift;
    return JSON::PP->new->pretty->canonical->encode($self->bindings);
}

1;
