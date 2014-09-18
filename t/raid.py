import unittest
from perfTest.Devices import RAID


class RaidTest(unittest.TestCase):
    def setUp(self):
        self.devs = ['/dev/sda','/dev/sdb']
        self.r = RAID('raid','/dev/md0','intelRaid', self.devs, 1,'software')
    def test(self):
        self.assertEqual(self.r.getRaidLevel(), 1)
        self.assertEqual(self.r.getType(), 'software')

if __name__ == '__main__':
    unittest.main()