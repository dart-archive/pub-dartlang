# -*- coding: utf-8 -*-
# Copyright (c) 2012, the Dart project authors.  Please see the AUTHORS file
# for details. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from cStringIO import StringIO
import tarfile

from testcase import TestCase
from models.readme import Readme

class ReadmeTest(TestCase):
    def test_extracts_readme_from_archive(self):
        self.assert_extracts_readme("README")
        self.assert_extracts_readme("README.md")
        self.assert_extracts_readme("README.jp.md")
        self.assert_extracts_readme("readme")
        self.assert_extracts_readme("readme.md")
        self.assert_extracts_readme("ReAdMe")

    def test_doesnt_extract_prefixed_readme(self):
        archive = self.readme_archive("NOT_README")
        self.assertIsNone(Readme.from_archive(archive))

    def test_chooses_readme_with_fewest_extensions(self):
        self.assert_extracts_readme(
            "README", ["README", "README.md", "README.md.jp"])
        self.assert_extracts_readme("README.md", ["README.md", "README.md.jp"])

    def test_chooses_readme_with_same_extensions_lexically(self):
        self.assert_extracts_readme(
            "README", ["readme", "README", "READme"])
        self.assert_extracts_readme("README.md", ["README.md", "README.zx"])
        self.assert_extracts_readme("README.md", ["README.md", "readme.a"])

    def test_decodes_valid_utf_8(self):
        archive = self.archive({'README': 'This is a R\303\213ADM\303\213.'})
        readme = Readme.from_archive(archive)
        self.assertEqual(u'This is a RËADMË.', readme.text)

    def test_tries_to_decode_invalid_utf_8(self):
        archive = self.archive({'README': 'This is a R\300ADM\300.'})
        readme = Readme.from_archive(archive)
        self.assertEqual(u'This is a R�ADM�.', readme.text)

    def test_infers_format_from_filename(self):
        readme = Readme("This is a README.", "README")
        self.assertEqual(Readme.Format.TEXT, readme.format)

        readme = Readme("This is a README.", "README.md")
        self.assertEqual(Readme.Format.MARKDOWN, readme.format)

        readme = Readme("This is a README.", "README.jp.md")
        self.assertEqual(Readme.Format.MARKDOWN, readme.format)

        readme = Readme("This is a README.", "README.md.jp")
        self.assertEqual(Readme.Format.TEXT, readme.format)

    def test_wraps_plain_text_readme_in_pre(self):
        readme = Readme("This is a *<README>*.", "README")
        self.assertEqual("<pre>This is a *&lt;README&gt;*.</pre>",
                         readme.render())

    def test_renders_markdown_readme(self):
        readme = Readme("This is a *<README>*.", "README.md")
        self.assertEqual("<p>This is a <em>&lt;README&gt;</em>.</p>",
                         readme.render())

        readme = Readme("This is a *<README>*.", "readme.MD")
        self.assertEqual("<p>This is a <em>&lt;README&gt;</em>.</p>",
                         readme.render())

    def assert_extracts_readme(self, chosen, names=None):
        """Assert that the given README is extracted from an archive.

        If no names are passed, creates an archive with a single README."""
        archive = self.readme_archive(*(names or [chosen]))
        readme = Readme.from_archive(archive)
        self.assertIsNotNone(readme)
        self.assertEqual('This is a README named "%s".' % chosen, readme.text)
        self.assertEqual(chosen, readme.filename)

    def readme_archive(self, *names):
        """Return an archive containing README files with the given names."""
        return self.archive({name: 'This is a README named "%s".' % name
                             for name in names})
