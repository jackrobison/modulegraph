"""
Test for import machinery
"""
import unittest
import sys
import textwrap
import subprocess
import os
from modulegraph import modulegraph

class TestNativeImport (unittest.TestCase):
    # The tests check that Python's import statement
    # works as these tests expect.

    def importModule(self, name):
        if '.' in name:
            script = textwrap.dedent("""\
                try:
                    import %s
                except ImportError:
                    import %s
                print (%s.__name__)
            """) %(name, name.rsplit('.', 1)[0], name)
        else:
            script = textwrap.dedent("""\
                import %s
                print (%s.__name__)
            """) %(name, name)

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

        sts = p.wait()

        if sts != 0:
            print data
        self.assertEquals(sts, 0)
        return data
        

    def testRootModule(self):
        m = self.importModule('mod')
        self.assertEquals(m, 'mod')

    def testRootPkg(self):
        m = self.importModule('pkg')
        self.assertEquals(m, 'pkg')

    def testSubModule(self):
        m = self.importModule('pkg.mod')
        self.assertEquals(m, 'pkg.mod')

    if sys.version_info[0] == 2:
        def testOldStyle(self):
            m = self.importModule('pkg.oldstyle.mod')
            self.assertEquals(m, 'pkg.mod')
    else:
        # python3 always has __future__.absolute_import
        def testOldStyle(self):
            m = self.importModule('pkg.oldstyle.mod')
            self.assertEquals(m, 'mod')

    def testNewStyle(self):
        m = self.importModule('pkg.toplevel.mod')
        self.assertEquals(m, 'mod')
    
    def testRelativeImport(self):
        m = self.importModule('pkg.relative.mod')
        self.assertEquals(m, 'pkg.mod')

        m = self.importModule('pkg.subpkg.relative.mod')
        self.assertEquals(m, 'pkg.mod')

        m = self.importModule('pkg.subpkg.mod2.mod')
        self.assertEquals(m, 'pkg.sub2.mod')


class TestModuleGraphImport (unittest.TestCase):
    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, value, types):
            if not isinstance(value, types):
                self.fail("%r is not an instance of %r", value, types)

    def setUp(self):
        root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'testpkg-relimport')
        self.mf = modulegraph.ModuleGraph(path=[ root ] + sys.path)
        #self.mf.debug = 999
        self.mf.run_script(os.path.join(root, 'script.py'))


    def testRootModule(self):
        node = self.mf.findNode('mod')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'mod')

    def testRootPkg(self):
        node = self.mf.findNode('pkg')
        self.assertIsInstance(node, modulegraph.Package)
        self.assertEquals(node.identifier, 'pkg')

    def testSubModule(self):
        node = self.mf.findNode('pkg.mod')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'pkg.mod')

    if sys.version_info[0] == 2:
        def testOldStyle(self):
            node = self.mf.findNode('pkg.oldstyle')
            self.assertIsInstance(node, modulegraph.SourceModule)
            self.assertEquals(node.identifier, 'pkg.oldstyle')
            sub = [ n for n in self.mf.get_edges(node)[0] if n.identifier != '__future__' ][0]
            self.assertEquals(sub.identifier, 'pkg.mod')
    else:
        # python3 always has __future__.absolute_import
        def testOldStyle(self):
            node = self.mf.findNode('pkg.oldstyle')
            self.assertIsInstance(node, modulegraph.SourceModule)
            self.assertEquals(node.identifier, 'pkg.oldstyle')
            sub = [ n for n in self.mf.get_edges(node)[0] if n.identifier != '__future__' ][0]
            self.assertEquals(sub.identifier, 'mod')

    def testNewStyle(self):
        node = self.mf.findNode('pkg.toplevel')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'pkg.toplevel')
        sub = [ n for n in self.mf.get_edges(node)[0] if n.identifier != '__future__' ][0]
        self.assertEquals(sub.identifier, 'mod')
    
    def testRelativeImport(self):
        node = self.mf.findNode('pkg.relative')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'pkg.relative')
        sub = [ n for n in self.mf.get_edges(node)[0] if n.identifier != '__future__' ][0]
        self.assertIsInstance(sub, modulegraph.Package)
        self.assertEquals(sub.identifier, 'pkg')

        node = self.mf.findNode('pkg.subpkg.relative')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'pkg.subpkg.relative')
        sub = [ n for n in self.mf.get_edges(node)[0] if n.identifier != '__future__' ][0]
        self.assertIsInstance(sub, modulegraph.Package)
        self.assertEquals(sub.identifier, 'pkg')

        node = self.mf.findNode('pkg.subpkg.mod2')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'pkg.subpkg.mod2')
        sub = [ n for n in self.mf.get_edges(node)[0] if n.identifier != '__future__' ][0]
        self.assertIsInstance(sub, modulegraph.SourceModule)
        self.assertEquals(sub.identifier, 'pkg.sub2.mod')


class TestRegressions (unittest.TestCase):
    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, value, types):
            if not isinstance(value, types):
                self.fail("%r is not an instance of %r", value, types)

    def setUp(self):
        root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'testpkg-regr1')
        self.mf = modulegraph.ModuleGraph(path=[ root ] + sys.path)
        self.mf.run_script(os.path.join(root, 'main_script.py'))

    def testRegr1(self):
        node = self.mf.findNode('pkg.a')
        self.assertIsInstance(node, modulegraph.SourceModule)
        node = self.mf.findNode('pkg.b')
        self.assertIsInstance(node, modulegraph.SourceModule)


    def testMissingPathEntry(self):
        root = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'nosuchdirectory')
        try:
            mf = modulegraph.ModuleGraph(path=[ root ] + sys.path)
        except os.error:
            self.fail('modulegraph initialiser raises os.error')

if __name__ == "__main__":
    unittest.main()
