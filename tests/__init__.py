"""Unit tests for pipeline."""

import mock
import unittest

class Pipeline(unittest.TestCase):                                                  
  def testCheck(self):
    m = mock.Mock()
    m.return_value = 10

    ret = m()

    self.assertEqual(ret, 10)

