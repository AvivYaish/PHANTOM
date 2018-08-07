import pytest
from lazy_set import LazySet


class TestLazySet:
    """
    Test suite for the LazySet data structure.
    """

    EMPTY_SET = set()
    SET1 = {1, 2, 3}
    SET2 = {4, 5, 6}
    ALL_SETS = [EMPTY_SET, SET1, SET2]
    EMPTY_SET_LIST = list([EMPTY_SET])
    SET_LIST_1 = [{4, 5, 6}, {7, 8, 9}, {10, 11, 12}]
    SET_LIST_2 = [{4, 7}, {3, 11}, {6}, {4, 9}]
    ALL_LISTS = [EMPTY_SET_LIST, SET_LIST_1, SET_LIST_2]

    @staticmethod
    def basic_test(test_set, valid_set):
        """
        The basic set of tests.
        Given a "valid" set, valid_set, and an instance of a set-like type that is supposed to be identical, test_set,
        checks that indeed test_set is identical to valid_set and that test_set supports the basic set operations.
        """
        # prepare data for test
        larger_set = valid_set.union({'a'})
        smaller_set = valid_set.copy()
        if len(valid_set) > 0:
            smaller_set.pop()
        disjoint_set = larger_set - valid_set

        # membership tests
        for item in valid_set:
            assert item in test_set
        for item in disjoint_set:
            assert item not in test_set

        # iteration tests
        comparison_set = set()
        for item in test_set:
            comparison_set.add(item)
        assert comparison_set == valid_set

        # comparison operators tests
        assert test_set <= valid_set
        assert valid_set >= test_set

        assert test_set >= valid_set
        assert valid_set <= test_set

        assert test_set == valid_set
        assert valid_set == test_set

        assert test_set <= larger_set
        assert larger_set >= test_set

        assert test_set != larger_set
        assert larger_set != test_set

        assert test_set < larger_set
        assert larger_set > test_set

        assert test_set >= smaller_set
        assert smaller_set <= test_set

        assert (test_set != smaller_set) is (len(valid_set) > 0)
        assert (smaller_set != test_set) is (len(valid_set) > 0)

        assert (test_set > smaller_set) is (len(valid_set) > 0)
        assert (smaller_set < test_set) is (len(valid_set) > 0)

        # other tests
        assert len(test_set) == len(valid_set)
        assert test_set.isdisjoint(disjoint_set)
        assert test_set.isdisjoint(valid_set) is (len(valid_set) == 0)
        assert test_set.isdisjoint(larger_set) is (len(test_set) == 0)
        assert test_set.isdisjoint(smaller_set) is (len(smaller_set) == 0)

    @staticmethod
    def interleaving_test_iterator(base_set,
                                   negative_sets,
                                   positive_sets,
                                   more_negative_sets,
                                   more_positive_sets,
                                   intersection_sets,
                                   symmetric_difference_sets,
                                   update,
                                   numeric_operations):
        """
        Iterates on the test by alternatingly adding positive and negative sets
        to the LazySet and yielding the according LazySet and regular set.
        :param update: whether to use methods that update the LazySet in-place or not.
        :param numeric_operations: whether to use numeric-operation-style methods (e.g. |, -, etc') when creating
        the LazySet or not.
        """
        lazy_set = LazySet(base_set=base_set, negative_sets=negative_sets, positive_sets=positive_sets)
        regular_set = base_set.difference(*negative_sets).union(*positive_sets)
        yield lazy_set, regular_set  # "base" test
        yield lazy_set.copy(), regular_set
        yield lazy_set.copy_to_set(), regular_set
        yield lazy_set.copy().flatten(), regular_set
        yield lazy_set.copy().flatten(True), regular_set

        # re-run the test after each successive modification to the sets
        index = 0
        while index <= max(len(more_positive_sets), len(more_negative_sets)):
            if index < len(more_negative_sets):
                regular_set -= more_negative_sets[index]
                if update:
                    if numeric_operations:
                        lazy_set -= more_negative_sets[index]
                    else:
                        lazy_set.difference_update(more_negative_sets[index])
                else:
                    if numeric_operations:
                        lazy_set = lazy_set - more_negative_sets[index]
                    else:
                        lazy_set = lazy_set.difference(more_negative_sets[index])
                yield lazy_set, regular_set
                yield lazy_set.copy(), regular_set
                yield lazy_set.copy_to_set(), regular_set
                yield lazy_set.copy().flatten(), regular_set
                yield lazy_set.copy().flatten(True), regular_set

            if index < len(more_positive_sets):
                regular_set |= more_positive_sets[index]
                if update:
                    if numeric_operations:
                        lazy_set |= more_positive_sets[index]
                    else:
                        lazy_set.update(more_positive_sets[index])
                else:
                    if numeric_operations:
                        lazy_set = lazy_set | more_positive_sets[index]
                    else:
                        lazy_set = lazy_set.union(more_positive_sets[index])
                yield lazy_set, regular_set
                yield lazy_set.copy(), regular_set
                yield lazy_set.copy_to_set(), regular_set
                yield lazy_set.copy().flatten(), regular_set
                yield lazy_set.copy().flatten(True), regular_set

            if index < len(intersection_sets):
                regular_set &= intersection_sets[index]
                if update:
                    if numeric_operations:
                        lazy_set &= intersection_sets[index]
                    else:
                        lazy_set.intersection_update(intersection_sets[index])
                else:
                    if numeric_operations:
                        lazy_set = lazy_set & intersection_sets[index]
                    else:
                        lazy_set = lazy_set.intersection(intersection_sets[index])
                yield lazy_set, regular_set
                yield lazy_set.copy(), regular_set
                yield lazy_set.copy_to_set(), regular_set
                yield lazy_set.copy().flatten(), regular_set
                yield lazy_set.copy().flatten(True), regular_set

            if index < len(symmetric_difference_sets):
                regular_set ^= symmetric_difference_sets[index]
                if update:
                    if numeric_operations:
                        lazy_set ^= symmetric_difference_sets[index]
                    else:
                        lazy_set.symmetric_difference_update(symmetric_difference_sets[index])
                else:
                    if numeric_operations:
                        lazy_set = lazy_set ^ symmetric_difference_sets[index]
                    else:
                        lazy_set = lazy_set.symmetric_difference(symmetric_difference_sets[index])
                yield lazy_set, regular_set
                yield lazy_set.copy(), regular_set
                yield lazy_set.copy_to_set(), regular_set
                yield lazy_set.copy().flatten(), regular_set
                yield lazy_set.copy().flatten(True), regular_set

            index += 1

        # clear the sets and run the tests for the final time
        lazy_set.clear()
        regular_set.clear()
        yield lazy_set, regular_set
        yield lazy_set.copy(), regular_set
        yield lazy_set.copy_to_set(), regular_set
        yield lazy_set.copy().flatten(), regular_set
        yield lazy_set.copy().flatten(True), regular_set

    @pytest.mark.parametrize("base_set", ALL_SETS)
    @pytest.mark.parametrize("negative_sets", ALL_LISTS)
    @pytest.mark.parametrize("positive_sets", ALL_LISTS)
    @pytest.mark.parametrize("more_negative_sets", ALL_LISTS)
    @pytest.mark.parametrize("more_positive_sets", ALL_LISTS)
    @pytest.mark.parametrize("intersection_sets", ALL_LISTS)
    @pytest.mark.parametrize("symmetric_difference_sets", ALL_LISTS)
    @pytest.mark.parametrize("update", [False, True])
    @pytest.mark.parametrize("numeric_operations", [False, True])
    def test_interleaving_creation(self, base_set, negative_sets, positive_sets, more_positive_sets, more_negative_sets,
                                   intersection_sets, symmetric_difference_sets, update, numeric_operations):
        """
        Evaluates the basic test on each step of the gradual "building" of the LazySet.
        """
        for lazy_set, regular_set in TestLazySet.interleaving_test_iterator(base_set, negative_sets, positive_sets,
                                                                            more_negative_sets, more_positive_sets,
                                                                            intersection_sets,
                                                                            symmetric_difference_sets, update,
                                                                            numeric_operations):
            TestLazySet.basic_test(lazy_set, regular_set)

    def test_single_element_methods(self):
        """
        Tests the LazySet by adding and then removing single elements to it.
        """
        lazy_set = LazySet()
        regular_set = set()
        TestLazySet.basic_test(lazy_set, regular_set)

        elem1 = 1
        lazy_set.add(elem1)
        regular_set.add(elem1)
        TestLazySet.basic_test(lazy_set, regular_set)

        elem2 = '1'
        lazy_set.add(elem2)
        regular_set.add(elem2)
        TestLazySet.basic_test(lazy_set, regular_set)

        elem3 = None
        lazy_set.add(elem3)
        regular_set.add(elem3)
        TestLazySet.basic_test(lazy_set, regular_set)

        elem4 = float('inf')
        lazy_set.add(elem4)
        regular_set.add(elem4)
        TestLazySet.basic_test(lazy_set, regular_set)

        lazy_set.remove(elem2)
        regular_set.remove(elem2)
        TestLazySet.basic_test(lazy_set, regular_set)

        with pytest.raises(KeyError) as lazy_excinfo:
            lazy_set.remove(elem2)
        with pytest.raises(KeyError) as regular_excinfo:
            regular_set.remove(elem2)
        assert lazy_excinfo.type == regular_excinfo.type
        assert str(lazy_excinfo.value) == str(regular_excinfo.value)
        TestLazySet.basic_test(lazy_set, regular_set)

        lazy_set.discard(elem2)
        regular_set.discard(elem2)
        TestLazySet.basic_test(lazy_set, regular_set)

        lazy_set.discard(elem1)
        regular_set.discard(elem1)
        TestLazySet.basic_test(lazy_set, regular_set)

        lazy_set.add(elem2)
        regular_set.add(elem2)
        TestLazySet.basic_test(lazy_set, regular_set)

        lazy_set.discard(elem2)
        regular_set.discard(elem2)
        TestLazySet.basic_test(lazy_set, regular_set)

        pop_elem = lazy_set.pop()
        regular_set.remove(pop_elem)
        TestLazySet.basic_test(lazy_set, regular_set)

        pop_elem = lazy_set.pop()
        regular_set.remove(pop_elem)
        TestLazySet.basic_test(lazy_set, regular_set)

        with pytest.raises(KeyError) as lazy_excinfo:
            lazy_set.pop()
        with pytest.raises(KeyError) as regular_excinfo:
            regular_set.pop()
        assert lazy_excinfo.type == regular_excinfo.type
