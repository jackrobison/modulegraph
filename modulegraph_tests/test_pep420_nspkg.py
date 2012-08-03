"""
Tests that deal with pep420 namespace packages.

PEP 420 is new in Python 3.3
"""
import os
import shutil
import sys
import subprocess
import unittest
import textwrap

from modulegraph import modulegraph

gRootDir = os.path.dirname(os.path.abspath(__file__))
gSrcDir = os.path.join(gRootDir, 'testpkg-pep420-namespace')

if sys.version_info[:2] >= (3,3):

    class TestPythonBehaviour (unittest.TestCase):
        def importModule(self, name):
            test_dir1 = os.path.join(gSrcDir, 'path1')
            test_dir2 = os.path.join(gSrcDir, 'path2')
            if '.' in name:
                script = textwrap.dedent("""\
                    import site
                    site.addsitedir(%r)
                    site.addsitedir(%r)
                    try:
                        import %s
                    except ImportError:
                        import %s
                    print (%s.__name__)
                """) %(test_dir1, test_dir2, name, name.rsplit('.', 1)[0], name)
            else:
                script = textwrap.dedent("""\
                    import site
                    site.addsitedir(%r)
                    site.addsitedir(%r)
                    import %s
                    print (%s.__name__)
                """) %(test_dir1, test_dir2, name, name)

            p = subprocess.Popen([sys.executable, '-c', script], 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        'testpkg-relimport'),
            )
            data = p.communicate()[0]
            if sys.version_info[0] != 2:
                data = data.decode('UTF-8')
            data = data.strip()
            if data.endswith(' refs]'):
                data = data.rsplit('\n', 1)[0].strip()

            sts = p.wait()

            if sts != 0:
                print (data)
                self.fail("import of %r failed"%(name,))

            return data

        def testToplevel(self):
            m = self.importModule('package.sub1')
            self.assertEqual(m, 'package.sub1')

            m = self.importModule('package.sub2')
            self.assertEqual(m, 'package.sub2')

        def testSub(self):
            m = self.importModule('package.subpackage.sub')
            self.assertEqual(m, 'package.subpackage.sub')

    class TestModuleGraphImport (unittest.TestCase):
        if not hasattr(unittest.TestCase, 'assertIsInstance'):
            def assertIsInstance(self, value, types):
                if not isinstance(value, types):
                    self.fail("%r is not an instance of %r", value, types)

        def setUp(self):
            self.mf = modulegraph.ModuleGraph(path=[
                    os.path.join(gSrcDir, 'path1'),
                    os.path.join(gSrcDir, 'path2'),
                ] + sys.path)


        def testRootPkg(self):
            self.mf.import_hook('package')

            node = self.mf.findNode('package')
            self.assertIsInstance(node, modulegraph.Package)
            self.assertEqual(node.identifier, 'package')
            self.assertEqual(node.filename, '-')

        def testRootPkgModule(self):
            self.mf.import_hook('package.sub1')

            node = self.mf.findNode('package.sub1')
            self.assertIsInstance(node, modulegraph.SourceModule)
            self.assertEqual(node.identifier, 'package.sub1')

            node = self.mf.findNode('package.sub2')
            self.assertIsInstance(node, modulegraph.SourceModule)
            self.assertEqual(node.identifier, 'package.sub2')

        def testSubRootPkgModule(self):
            self.mf.import_hook('package.subpackage.sub')

            node = self.mf.findNode('package.subpackage.sub')
            self.assertIsInstance(node, modulegraph.SourceModule)
            self.assertEqual(node.identifier, 'package.subpackage.sub')

            node = self.mf.findNode('package')
            self.assertIsInstance(node, modulegraph.Package)


if __name__ == "__main__":
    unittest.main()
