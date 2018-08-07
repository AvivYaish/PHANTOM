# LazySet

A collection that tries to imitate a "chained" difference and union of sets and various other operations are performed
lazily:

Given a base set, an iterable of sets to subtract from the base set, and an iterable of sets to now add to it
(note that the order is important!), a LazySet will act exactly like a regular set and supports all the basic
operations, but without actually performing any state-changing unions or differences to any of the participating
sets (that take O(number of items in all sets)).

Instead, the LazySet goes over all participating sets according to their order to check if an item is contained
in it, thus giving a better run time in some cases for most operations. For example, if the LazySet used is after
initialization and no modifying operations were used on it, containment checking takes O(number of participating sets).

Note that when using only difference and union operations, this collection is the set equivalent of ChainMap, so it can
also be called ChainSet.
