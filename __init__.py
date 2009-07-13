# Copyright (c) 2003-2005 Jimmy Retzlaff, 2008 Konstantin Yegupov
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
pyUnRAR2 is a ctypes based wrapper around the free UnRAR.dll. 

It is an modified version of Jimmy Retzlaff's pyUnRAR - more simple,
stable and foolproof.
Notice that it has INCOMPATIBLE interface.

It enables reading and unpacking of archives created with the
RAR/WinRAR archivers. There is a low-level interface which is very
similar to the C interface provided by UnRAR. There is also a
higher level interface which makes some common operations easier.
"""

__version__ = '0.91'

try:
    WindowsError
    in_windows = True
except NameError:
    in_windows = False

if in_windows:
    from windows import RarFile
else:
    raise NotImplementedError('Only Windows is supported so far')
    

class RarInfo:
    """Represents a file header in an archive. Don't instantiate directly.
    Use only to obtain information about file.
    YOU CANNOT EXTRACT FILE CONTENTS USING THIS OBJECT.
    USE METHODS OF RarFile CLASS INSTEAD.

    Properties:
        index - index of file within the archive
        filename - name of the file in the archive including path (if any)
        datetime - file date/time as a struct_time suitable for time.strftime
        isdir - True if the file is a directory
        size - size in bytes of the uncompressed file
        comment - comment associated with the file

                  1030      521  50% 08-02-02 16:47  .....A.   119BE7CF m5b 2.9

    Note - this is not currently intended to be a Python file-like object.
    """

    def __init__(self, rarfile, index, headerData=None, unrar_v_lines=None):
        self.rarfile = rarfile
        self.index = index
        if headerData!=None:
            self.filename = headerData.FileName
            self.datetime = DosDateTimeToTimeTuple(headerData.FileTime)
            self.isdir = ((headerData.Flags & 0xE0) == 0xE0)
            self.size = headerData.UnpSize + (headerData.UnpSizeHigh << 32)
            if headerData.CmtState == 1:
                self.comment = headerData.CmtBuf.value
            else:
                self.comment = None
        elif unrar_v_lines!=None and len(unrar_v_lines)==2:
            self.filename = unrar_v_lines[0].strip()
            info = unrar_v_lines[1]
            self.size = int(info[:22])
            attr = info[53:60]
            self.isdir = 'D' in attr
            self.datetime = time.strptime(info[37:51], '%d-%m-%y %H:%M')
            self.comment = None


    def __str__(self):
        return '<RarInfo "%s" in "%s">' % (self.filename, self.rarfile.archiveName)



def condition2checker(condition):
    """Converts different condition types to callback"""
    if type(condition) in [str, unicode]:
        def smatcher(info):
            return fnmatch.fnmatch(info.filename, condition)
        return smatcher
    elif type(condition) in [list, tuple] and type(condition[0]) in [int, long]:
        def imatcher(info):
            return info.index in condition
        return imatcher
    elif callable(condition):
        return condition
    else:
        raise TypeError
