import os

import UnRAR2


def cleanup():
    if os.path.exists('test'):
        for filename in os.listdir('test'):
            os.remove(os.path.join('test', filename))
        os.removedirs('test')


# extract all the files in test.rar
cleanup()
UnRAR2.RarFile('test.rar').extract()
assert os.path.exists(r'test\test.txt')
assert os.path.exists(r'test\this.py')
cleanup()


# extract all the files in test.rar matching the wildcard *.txt
cleanup()
UnRAR2.RarFile('test.rar').extract('*.txt')
assert os.path.exists(r'test\test.txt')
assert not os.path.exists(r'test\this.py')
cleanup()


# check the name and size of each file, extracting small ones
cleanup()
archive = UnRAR2.RarFile('test.rar')
assert archive.comment == 'This is a test.'
archive.extract(lambda rarinfo: rarinfo.size <= 1024)
for rarinfo in archive.infoiter():
    if rarinfo.size <= 1024:
        assert rarinfo.size == os.stat(rarinfo.filename).st_size
assert file(r'test\test.txt', 'rt').read() == 'This is only a test.'
assert not os.path.exists(r'test\this.py')
cleanup()


# extract this.py, overriding it's destination
cleanup()
archive = UnRAR2.RarFile('test.rar')
def this2that(rarinfo):
    if rarinfo.filename.endswith('this.py'):
        return r'test\that.py'
    else:
        return False
archive.extract(this2that)
assert os.path.exists(r'test\that.py')
cleanup()


# extract test.txt to memory
cleanup()
archive = UnRAR2.RarFile('test.rar')
entries = UnRAR2.RarFile('test.rar').read_files('*test.txt')
assert len(entries)==1
assert entries[0][0].filename.endswith('test.txt')
assert entries[0][1]=='This is only a test.'

# make sure docstring examples are working
import doctest
doctest.testmod(UnRAR2)

# update documentation
import pydoc
pydoc.writedoc(UnRAR2)

# cleanup
os.remove('__init__.pyc')
