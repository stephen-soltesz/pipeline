"""Unit tests for pipeline."""

import mock
import unittest
import sys

import src.lineview as lineview

class View(unittest.TestCase):
  """Test class for pipeline server."""

  def test_Limits(self):
    m_test = mock.Mock()
    m_test.return_value = 10

    limits = lineview.Limits()

    self.assertEqual(limits.x_max, 0)
    self.assertEqual(limits.x_min, sys.maxint)
    self.assertEqual(limits.y_max, 0)
    self.assertEqual(limits.y_min, sys.maxint)

