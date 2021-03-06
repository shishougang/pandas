from datetime import datetime
import pickle
import unittest

import numpy as np

import pandas.core.datetools as datetools
from pandas.tseries.offsets import generate_range
from pandas.core.index import Index
from pandas.tseries.index import DatetimeIndex

from pandas.tseries.index import bdate_range, date_range
import pandas.tseries.tools as tools

def eq_gen_range(kwargs, expected):
    rng = generate_range(**kwargs)
    assert(np.array_equal(list(rng), expected))

START, END = datetime(2009, 1, 1), datetime(2010, 1, 1)

class TestGenRangeGeneration(unittest.TestCase):
    def test_generate(self):
        rng1 = list(generate_range(START, END, offset=datetools.bday))
        rng2 = list(generate_range(START, END, time_rule='B'))
        self.assert_(np.array_equal(rng1, rng2))

    def test_1(self):
        eq_gen_range(dict(start=datetime(2009, 3, 25), periods=2),
                     [datetime(2009, 3, 25), datetime(2009, 3, 26)])

    def test_2(self):
        eq_gen_range(dict(start=datetime(2008, 1, 1),
                          end=datetime(2008, 1, 3)),
                     [datetime(2008, 1, 1),
                      datetime(2008, 1, 2),
                      datetime(2008, 1, 3)])

    def test_3(self):
        eq_gen_range(dict(start = datetime(2008, 1, 5),
                          end = datetime(2008, 1, 6)),
                     [])

class TestDateRange(unittest.TestCase):

    def setUp(self):
        self.rng = bdate_range(START, END)

    def test_constructor(self):
        rng = bdate_range(START, END, freq=datetools.bday)
        rng = bdate_range(START, periods=20, freq=datetools.bday)
        rng = bdate_range(end=START, periods=20, freq=datetools.bday)
        self.assertRaises(ValueError, date_range, '2011-1-1', '2012-1-1', 'B')
        self.assertRaises(ValueError, bdate_range, '2011-1-1', '2012-1-1', 'B')

    def test_cached_range(self):
        rng = DatetimeIndex._cached_range(START, END,
                                          offset=datetools.bday)
        rng = DatetimeIndex._cached_range(START, periods=20,
                                          offset=datetools.bday)
        rng = DatetimeIndex._cached_range(end=START, periods=20,
                                          offset=datetools.bday)

        self.assertRaises(Exception, DatetimeIndex._cached_range, START, END)

        self.assertRaises(Exception, DatetimeIndex._cached_range, START,
                          freq=datetools.bday)

        self.assertRaises(Exception, DatetimeIndex._cached_range, end=END,
                          freq=datetools.bday)

        self.assertRaises(Exception, DatetimeIndex._cached_range, periods=20,
                          freq=datetools.bday)

    def test_cached_range_bug(self):
        rng = date_range('2010-09-01 05:00:00', periods=50,
                         freq=datetools.DateOffset(hours=6))
        self.assertEquals(len(rng), 50)
        self.assertEquals(rng[0], datetime(2010, 9, 1, 5))

    def test_comparison(self):
        d = self.rng[10]

        comp = self.rng > d
        self.assert_(comp[11])
        self.assert_(not comp[9])

    def test_copy(self):
        cp = self.rng.copy()
        repr(cp)
        self.assert_(cp.equals(self.rng))

    def test_repr(self):
        # only really care that it works
        repr(self.rng)

    def test_getitem(self):
        smaller = self.rng[:5]
        self.assert_(np.array_equal(smaller, self.rng.view(np.ndarray)[:5]))
        self.assertEquals(smaller.offset, self.rng.offset)

        sliced = self.rng[::5]
        self.assertEquals(sliced.offset, datetools.bday * 5)

        fancy_indexed = self.rng[[4, 3, 2, 1, 0]]
        self.assertEquals(len(fancy_indexed), 5)
        self.assert_(isinstance(fancy_indexed, DatetimeIndex))
        self.assert_(fancy_indexed.freq is None)

        # 32-bit vs. 64-bit platforms
        self.assertEquals(self.rng[4], self.rng[np.int_(4)])

    def test_getitem_matplotlib_hackaround(self):
        values = self.rng[:, None]
        expected = self.rng.values[:, None]
        self.assert_(np.array_equal(values, expected))

    def test_shift(self):
        shifted = self.rng.shift(5)
        self.assertEquals(shifted[0], self.rng[5])
        self.assertEquals(shifted.offset, self.rng.offset)

        shifted = self.rng.shift(-5)
        self.assertEquals(shifted[5], self.rng[0])
        self.assertEquals(shifted.offset, self.rng.offset)

        shifted = self.rng.shift(0)
        self.assertEquals(shifted[0], self.rng[0])
        self.assertEquals(shifted.offset, self.rng.offset)

        rng = date_range(START, END, freq=datetools.bmonthEnd)
        shifted = rng.shift(1, freq=datetools.bday)
        self.assertEquals(shifted[0], rng[0] + datetools.bday)

    def test_pickle_unpickle(self):
        pickled = pickle.dumps(self.rng)
        unpickled = pickle.loads(pickled)

        self.assert_(unpickled.offset is not None)

    def test_union(self):
        # overlapping
        left = self.rng[:10]
        right = self.rng[5:10]

        the_union = left.union(right)
        self.assert_(isinstance(the_union, DatetimeIndex))

        # non-overlapping, gap in middle
        left = self.rng[:5]
        right = self.rng[10:]

        the_union = left.union(right)
        self.assert_(isinstance(the_union, Index))

        # non-overlapping, no gap
        left = self.rng[:5]
        right = self.rng[5:10]

        the_union = left.union(right)
        self.assert_(isinstance(the_union, DatetimeIndex))

        # order does not matter
        self.assert_(np.array_equal(right.union(left), the_union))

        # overlapping, but different offset
        rng = date_range(START, END, freq=datetools.bmonthEnd)

        the_union = self.rng.union(rng)
        self.assert_(isinstance(the_union, DatetimeIndex))

    def test_outer_join(self):
        # should just behave as union

        # overlapping
        left = self.rng[:10]
        right = self.rng[5:10]

        the_join = left.join(right, how='outer')
        self.assert_(isinstance(the_join, DatetimeIndex))

        # non-overlapping, gap in middle
        left = self.rng[:5]
        right = self.rng[10:]

        the_join = left.join(right, how='outer')
        self.assert_(isinstance(the_join, DatetimeIndex))
        self.assert_(the_join.freq is None)

        # non-overlapping, no gap
        left = self.rng[:5]
        right = self.rng[5:10]

        the_join = left.join(right, how='outer')
        self.assert_(isinstance(the_join, DatetimeIndex))

        # overlapping, but different offset
        rng = date_range(START, END, freq=datetools.bmonthEnd)

        the_join = self.rng.join(rng, how='outer')
        self.assert_(isinstance(the_join, DatetimeIndex))
        self.assert_(the_join.freq is None)

    def test_union_not_cacheable(self):
        rng = date_range('1/1/2000', periods=50, freq=datetools.Minute())
        rng1 = rng[10:]
        rng2 = rng[:25]
        the_union = rng1.union(rng2)
        self.assert_(the_union.equals(rng))

        rng1 = rng[10:]
        rng2 = rng[15:35]
        the_union = rng1.union(rng2)
        expected = rng[10:]
        self.assert_(the_union.equals(expected))

    def test_intersection(self):
        rng = date_range('1/1/2000', periods=50, freq=datetools.Minute())
        rng1 = rng[10:]
        rng2 = rng[:25]
        the_int = rng1.intersection(rng2)
        expected = rng[10:25]
        self.assert_(the_int.equals(expected))
        self.assert_(isinstance(the_int, DatetimeIndex))
        self.assert_(the_int.offset == rng.offset)

        the_int = rng1.intersection(rng2.view(DatetimeIndex))
        self.assert_(the_int.equals(expected))

        # non-overlapping
        the_int = rng[:10].intersection(rng[10:])
        expected = DatetimeIndex([])
        self.assert_(the_int.equals(expected))

    def test_intersection_bug(self):
        # GH #771
        a = bdate_range('11/30/2011','12/31/2011')
        b = bdate_range('12/10/2011','12/20/2011')
        result = a.intersection(b)
        self.assert_(result.equals(b))

    def test_summary(self):
        self.rng.summary()
        self.rng[2:2].summary()
        try:
            import pytz
            bdate_range('1/1/2005', '1/1/2009', tz=pytz.utc).summary()
        except Exception:
            pass

    def test_misc(self):
        end = datetime(2009, 5, 13)
        dr = bdate_range(end=end, periods=20)
        firstDate = end - 19 * datetools.bday

        assert len(dr) == 20
        assert dr[0] == firstDate
        assert dr[-1] == end

    def test_date_parse_failure(self):
        badly_formed_date = '2007/100/1'
        self.assertRaises(ValueError, bdate_range, start=badly_formed_date,
                          periods=10)
        self.assertRaises(ValueError, bdate_range, end=badly_formed_date,
                          periods=10)
        self.assertRaises(ValueError, bdate_range, badly_formed_date,
                          badly_formed_date)

    def test_equals(self):
        self.assertFalse(self.rng.equals(list(self.rng)))

    def test_daterange_bug_456(self):
        # GH #456
        rng1 = bdate_range('12/5/2011', '12/5/2011')
        rng2 = bdate_range('12/2/2011', '12/5/2011')
        rng2.offset = datetools.BDay()

        result = rng1.union(rng2)
        self.assert_(isinstance(result, DatetimeIndex))

    def test_error_with_zero_monthends(self):
        self.assertRaises(ValueError, date_range, '1/1/2000', '1/1/2001',
                          freq=datetools.MonthEnd(0))

    def test_range_bug(self):
        # GH #770
        offset = datetools.DateOffset(months=3)
        result = date_range("2011-1-1", "2012-1-31", freq=offset)

        start = datetime(2011, 1, 1)
        exp_values = [start + i * offset for i in range(5)]
        self.assert_(np.array_equal(result, DatetimeIndex(exp_values)))




if __name__ == '__main__':
    import nose
    nose.runmodule(argv=[__file__,'-vvs','-x','--pdb', '--pdb-failure'],
                   exit=False)
