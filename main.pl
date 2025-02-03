use strict;
use warnings;
use JSON;
use File::Slurp;
use Regexp::Optimizer;

print Regexp::Optimizer->new->optimize(qr(@{[ join("|", @{[ grep {!/cc$/} map { lc($_ =~ s/^\s+|\s.*//r) } map { @{ $_->{Alias} }, $_->{Name} } @{ decode_json(scalar read_file("instructions.json")) } ]}) ]})) =~ s/^\(\?\^:\(\?\^:/\\b\(\?i\)\(v\)\?\(/r =~ s/\)$/\\b/r, "\n";

