import unittest
from perfTest.Devices import RAID


class RaidTest(unittest.TestCase):
    def setUp(self):
        self.conf =  infile = open('raid.conf', 'r')
        self.r = RAID('raid','/dev/md0','intelRaid', self.conf)
    def test(self):
        self.assertEqual(self.r.getRaidLevel(), 1)
        self.assertEqual(self.r.getType(), 'software')

if __name__ == '__main__':
    unittest.main()