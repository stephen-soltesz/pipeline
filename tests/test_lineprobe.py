"""Unit tests for pipeline."""

import mock
import unittest

import src.lineprobe as lineprobe

class Probe(unittest.TestCase):
  """Test class for pipeline client."""

  def test_StreamSocket(self):
    m_socket = mock.Mock()
    expected_calls = 6
    returned_calls = 0

    with mock.patch('src.lineprobe.pipeline.socket', m_socket,
        create=True) as sock:
      client = lineprobe.pipeline.StreamSocket(lineprobe.pipeline.HOST,
                                               lineprobe.pipeline.PORT)
      client.wfile.write("OK")
      returned_calls = len(sock.mock_calls)

    self.assertEqual(expected_calls, returned_calls)

  def test_connect_to_grapher(self):
    m_streamsocket = mock.Mock()
    expected_calls = 2
    returned_calls = 0

    client = lineprobe.connect_to_grapher(m_streamsocket)
    client.wfile.write("OK")
    returned_calls = len(m_streamsocket.mock_calls)

    self.assertEqual(expected_calls, returned_calls)

