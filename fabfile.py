"""
Fabric fabfile for Davies cave survey package.

Run `pip install fabric` to install, then `fab --list` to see available commands.
"""

from fabric.api import local, lcd, with_settings


def test():
    """Run project unit tests."""
    local('python -m unittest discover -v -s tests')
unittest = test


@with_settings(warn_only=True)
def pep8():
    """Check source for PEP8 conformance."""
    local('pep8 --max-line-length=120 davies')


def precommit():
    """Run pre-commit unit tests and lint checks."""
    pep8()
    local('pylint -f colorized --errors-only davies')
    test()


def lint(fmt='colorized'):
    """Run verbose PyLint on source. Optionally specify fmt=html for HTML output."""
    if fmt == 'html':
        outfile = 'pylint_report.html'
        local('pylint -f %s davies > %s || true' % (fmt, outfile))
        local('open %s' % outfile)
    else:
        local('pylint -f %s davies || true' % fmt)
pylint = lint


def clean():
    """Clean up generated files."""
    local('rm -rf dist')
    local('rm -f pylint_report.html')
    local('find . -name "*.pyc" | xargs rm')
    with lcd('docs'):
        local('make clean')


def release(version):
    """Perform git-flow release merging and PyPI upload."""
    clean()
    local('git co master')
    local('git merge --no-ff dev')
    local('git tag %s' % version)
    local('python setup.py sdist upload')


def doc(fmt='html'):
    """Build Sphinx HTML documentation."""
    with lcd('docs'):
        local('make %s' % fmt)
    if fmt == 'html':
        local('open docs/_build/html/index.html')
docs = doc
