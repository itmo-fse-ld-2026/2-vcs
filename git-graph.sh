#!/bin/bash

REPO_PATH="${1:-.}"
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Error: $REPO_PATH is not a git repository." >&2
    exit 1
fi

cd "$REPO_PATH" || exit

echo "digraph G {"
echo "  rankdir=TB;"
echo "  node [shape=box, style=filled, color=lightblue, fontname=\"Arial\", fontsize=10];"
echo "  edge [color=\"#666666\", arrowhead=vee];"

# Using a null delimiter (\0) in git log is safer for complex messages
git log --all --pretty=format:"%h|%p|%an|%d|%s%n" | perl -F'\|' -lane '
    next if $#F < 4;
    my ($hash, $parents, $author, $refs, $msg) = @F;
    
    # Escape quotes and backslashes for DOT
    $msg =~ s/\\/\\\\/g;
    $msg =~ s/\"/\\\"/g;
    $refs =~ s/[() ]//g;

    my $style = "";
    if ($refs) {
        $style = qq(, color="gold", style="filled,bold");
        $msg = "[$refs]\\n$msg";
    }

    # Print Node
    print qq(  "$hash" [label="$hash ($author)\\n$msg"$style];);

    # Print Edges
    my @parent_list = split(/\s+/, $parents);
    foreach my $p (@parent_list) {
        if ($p =~ /^[a-f0-9]+$/) {
            # In Git DAGs, parents are usually the "source" of the arrow
            print qq(  "$p" -> "$hash";);
        }
    }
'

echo "}"