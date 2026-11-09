import unittest

import gitara


class PackageTests(unittest.TestCase):
    def test_import_gitara(self) -> None:
        self.assertEqual(gitara.__name__, "gitara")
