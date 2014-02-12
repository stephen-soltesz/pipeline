"""Unit tests for pipeline."""

import mock
import unittest

class Pipeline(unittest.TestCase):
  """Test class for pipeline server."""

  def testCheck(self):
    m_test = mock.Mock()
    m_test.return_value = 10

    ret = m_test()

    self.assertEqual(ret, 10)

