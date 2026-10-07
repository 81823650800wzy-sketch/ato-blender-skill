"""Synthetic invariants only; these fixtures are not production art or mattes."""
import unittest
import numpy as np
from PIL import Image
from contour_parts import partition, validate_partition, assemble, transform


class ContourTests(unittest.TestCase):
    def setUp(self):
        y, x = np.mgrid[:48, :64]
        self.hand = (((x-25)**2+(y-24)**2) < 120).astype(np.uint8)*255
        self.city = (y > 18+(x//7)%3*5).astype(np.uint8)*255
        self.pieces, _ = partition([self.hand, self.city])
        self.target = Image.fromarray(np.stack([x*4, y*5, (x+y)*2], axis=-1).astype(np.uint8)).convert('RGBA')
        self.base = Image.new('RGBA', (64,48), 'black')
        self.specs = [{'_mask': Image.fromarray(m), 'start': i*.1,
                       'end': .6+i*.1, 'dx': 30, 'dy': -20, 'angle': 12, 'scale': .7}
                      for i, (_,m) in enumerate(self.pieces)]

    def test_partition_priority_and_complete_coverage(self):
        report = validate_partition([m for _,m in self.pieces])
        self.assertEqual(report['uncovered_pixels'], 0)
        np.testing.assert_array_equal(self.pieces[0][1], self.hand)
        self.assertFalse(np.any((self.pieces[1][1]>0) & (self.hand>0)))

    def test_reject_incomplete_and_overlap(self):
        for masks in ([self.hand], [np.full_like(self.hand,255),self.hand]):
            with self.assertRaises(ValueError): validate_partition(masks)

    def test_empty_duplicate_skipped(self):
        _, skipped = partition([self.hand,self.hand,np.zeros_like(self.hand)])
        self.assertEqual(skipped, [1,2])

    def test_before_and_after(self):
        np.testing.assert_array_equal(assemble(self.target,self.base,self.specs,-1),self.base)
        np.testing.assert_array_equal(assemble(self.target,self.base,self.specs,2),self.target)

    def test_foreground_remains_unique(self):
        fg = Image.new('RGBA', self.target.size, (220,0,0,0))
        fg.putalpha(Image.fromarray(self.hand))
        result = np.asarray(assemble(self.target,self.base,self.specs,.4,fg))
        self.assertTrue(np.all(result[self.hand>0] == np.array([220,0,0,255])))

    def test_transform_endpoint_exact(self):
        np.testing.assert_array_equal(transform(self.target,self.specs[0],1),self.target)

    def test_dimension_mismatch_rejected(self):
        with self.assertRaises(ValueError): partition([self.hand, np.zeros((2,2))])


if __name__ == '__main__': unittest.main()
