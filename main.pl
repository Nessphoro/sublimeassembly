use strict;
use warnings;
use JSON;
use File::Slurp;
use Regexp::Optimizer;

my $json_text = read_file("instructions.json");

my @words = grep {!/cc/} map {
    my $i = $_;
    $i =~ s/^\s+|\s.*//g;
    $i = lc $i;
} map { @{ $_->{Alias} }, $_->{Name} } @{ decode_json($json_text) };

my $regex = Regexp::Optimizer->new->optimize(qr/@{[ join("|", @words) ]}/);
$regex =~ s/^\(\?\^:\(\?\^:/\\b\(\?i\)\(v\)\?\(/;
$regex =~ s/\)$/\\b/;

print $regex, "\n";

