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

from __future__ import generators
__version__ = '0.9'



import fnmatch
import os
import Queue
import time

import ctypes.wintypes

# Low level interface - see UnRARDLL\UNRARDLL.TXT

ERAR_END_ARCHIVE = 10
ERAR_NO_MEMORY = 11
ERAR_BAD_DATA = 12
ERAR_BAD_ARCHIVE = 13
ERAR_UNKNOWN_FORMAT = 14
ERAR_EOPEN = 15
ERAR_ECREATE = 16
ERAR_ECLOSE = 17
ERAR_EREAD = 18
ERAR_EWRITE = 19
ERAR_SMALL_BUF = 20
ERAR_UNKNOWN = 21

RAR_OM_LIST = 0
RAR_OM_EXTRACT = 1

RAR_SKIP = 0
RAR_TEST = 1
RAR_EXTRACT = 2

RAR_VOL_ASK = 0
RAR_VOL_NOTIFY = 1

RAR_DLL_VERSION = 3

# enum UNRARCALLBACK_MESSAGES
UCM_CHANGEVOLUME = 0
UCM_PROCESSDATA = 1
UCM_NEEDPASSWORD = 2

try:
    unrar = ctypes.WinDLL(os.path.join(os.path.split(__file__)[0], 'UnRARDLL', 'unrar.dll'))
except WindowsError:
    unrar = ctypes.WinDLL('unrar.dll')

class RAROpenArchiveDataEx(ctypes.Structure):
    def __init__(self, ArcName=None, ArcNameW=u'', OpenMode=RAR_OM_LIST):
        self.CmtBuf = ctypes.c_buffer(64*1024)
        ctypes.Structure.__init__(self, ArcName=ArcName, ArcNameW=ArcNameW, OpenMode=OpenMode, _CmtBuf=ctypes.addressof(self.CmtBuf), CmtBufSize=ctypes.sizeof(self.CmtBuf))

    _fields_ = [
                ('ArcName', ctypes.c_char_p),
                ('ArcNameW', ctypes.c_wchar_p),
                ('OpenMode', ctypes.c_uint),
                ('OpenResult', ctypes.c_uint),
                ('_CmtBuf', ctypes.c_voidp),
                ('CmtBufSize', ctypes.c_uint),
                ('CmtSize', ctypes.c_uint),
                ('CmtState', ctypes.c_uint),
                ('Flags', ctypes.c_uint),
                ('Reserved', ctypes.c_uint*32),
               ]

class RARHeaderDataEx(ctypes.Structure):
    def __init__(self):
        self.CmtBuf = ctypes.c_buffer(64*1024)
        ctypes.Structure.__init__(self, _CmtBuf=ctypes.addressof(self.CmtBuf), CmtBufSize=ctypes.sizeof(self.CmtBuf))

    _fields_ = [
                ('ArcName', ctypes.c_char*1024),
                ('ArcNameW', ctypes.c_wchar*1024),
                ('FileName', ctypes.c_char*1024),
                ('FileNameW', ctypes.c_wchar*1024),
                ('Flags', ctypes.c_uint),
                ('PackSize', ctypes.c_uint),
                ('PackSizeHigh', ctypes.c_uint),
                ('UnpSize', ctypes.c_uint),
                ('UnpSizeHigh', ctypes.c_uint),
                ('HostOS', ctypes.c_uint),
                ('FileCRC', ctypes.c_uint),
                ('FileTime', ctypes.c_uint),
                ('UnpVer', ctypes.c_uint),
                ('Method', ctypes.c_uint),
                ('FileAttr', ctypes.c_uint),
                ('_CmtBuf', ctypes.c_voidp),
                ('CmtBufSize', ctypes.c_uint),
                ('CmtSize', ctypes.c_uint),
                ('CmtState', ctypes.c_uint),
                ('Reserved', ctypes.c_uint*1024),
               ]

def DosDateTimeToTimeTuple(dosDateTime):
    """Convert an MS-DOS format date time to a Python time tuple.
    """
    dosDate = dosDateTime >> 16
    dosTime = dosDateTime & 0xffff
    day = dosDate & 0x1f
    month = (dosDate >> 5) & 0xf
    year = 1980 + (dosDate >> 9)
    second = 2*(dosTime & 0x1f)
    minute = (dosTime >> 5) & 0x3f
    hour = dosTime >> 11
    return time.localtime(time.mktime((year, month, day, hour, minute, second, 0, 1, -1)))

def _wrap(restype, function, argtypes):
    result = function
    result.argtypes = argtypes
    result.restype = restype
    return result

RARGetDllVersion = _wrap(ctypes.c_int, unrar.RARGetDllVersion, [])

RAROpenArchiveEx = _wrap(ctypes.wintypes.HANDLE, unrar.RAROpenArchiveEx, [ctypes.POINTER(RAROpenArchiveDataEx)])

RARReadHeaderEx = _wrap(ctypes.c_int, unrar.RARReadHeaderEx, [ctypes.wintypes.HANDLE, ctypes.POINTER(RARHeaderDataEx)])

_RARSetPassword = _wrap(ctypes.c_int, unrar.RARSetPassword, [ctypes.wintypes.HANDLE, ctypes.c_char_p])
def RARSetPassword(*args, **kwargs):
    _RARSetPassword(*args, **kwargs)

RARProcessFile = _wrap(ctypes.c_int, unrar.RARProcessFile, [ctypes.wintypes.HANDLE, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p])

RARCloseArchive = _wrap(ctypes.c_int, unrar.RARCloseArchive, [ctypes.wintypes.HANDLE])

UNRARCALLBACK = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint, ctypes.c_long, ctypes.c_long, ctypes.c_long)
RARSetCallback = _wrap(ctypes.c_int, unrar.RARSetCallback, [ctypes.wintypes.HANDLE, UNRARCALLBACK, ctypes.c_long])


# Higher level interface

class ArchiveHeaderBroken(Exception): pass
class InvalidRARArchive(Exception): pass
class FileOpenError(Exception): pass

RARExceptions = {
                 ERAR_NO_MEMORY : MemoryError,
                 ERAR_BAD_DATA : ArchiveHeaderBroken,
                 ERAR_BAD_ARCHIVE : InvalidRARArchive,
                 ERAR_EOPEN : FileOpenError,
                }

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

    Note - this is not currently intended to be a Python file-like object.
    """

    def __init__(self, rarfile, headerData, index):
        self.rarfile = rarfile
        self.index = index
        self.filename = headerData.FileName
        self.datetime = DosDateTimeToTimeTuple(headerData.FileTime)
        self.isdir = ((headerData.Flags & 0xE0) == 0xE0)
        self.size = headerData.UnpSize + (headerData.UnpSizeHigh << 32)
        if headerData.CmtState == 1:
            self.comment = headerData.CmtBuf.value
        else:
            self.comment = None

    def __str__(self):
        return '<RarInfo "%s" in "%s">' % (self.filename, self.rarfile.archiveName)


class PassiveReader:
    """Used for reading files to memory"""
    def __init__(self, usercallback = None):
        self.buf = []
        self.ucb = usercallback
    
    def _callback(self, msg, UserData, P1, P2):
        if msg == UCM_PROCESSDATA:
            data = (ctypes.c_char*P2).from_address(P1).raw
            if self.ucb!=None:
                self.ucb(data)
            else:
                self.buf.append(data)
        return 1
    
    def get_result(self):
        return ''.join(self.buf)

class RarFile:

    def __init__(self, archiveName, password=None):
        """Instantiate the archive.

        archiveName is the name of the RAR file.
        password is used to decrypt the files in the archive.

        Properties:
            comment - comment associated with the archive

        >>> print RarFile('test.rar').comment
        This is a test.
        """
        self.archiveName = archiveName
        archiveData = RAROpenArchiveDataEx(ArcNameW=self.archiveName, OpenMode=RAR_OM_EXTRACT)
        self._handle = RAROpenArchiveEx(ctypes.byref(archiveData))

        if archiveData.OpenResult != 0:
            raise RARExceptions[archiveData.OpenResult]

        if archiveData.CmtState == 1:
            self.comment = archiveData.CmtBuf.value
        else:
            self.comment = None

        if password:
            RARSetPassword(self._handle, password)

    def __del__(self):
        if self._handle and RARCloseArchive:
            RARCloseArchive(self._handle)

    def infoiter(self):
        """Iterate over all the files in the archive, generating RarInfos.

        >>> import os
        >>> for fileInArchive in RarFile('test.rar').infoiter():
        ...     print os.path.split(fileInArchive.filename)[-1],
        ...     print fileInArchive.isdir,
        ...     print fileInArchive.size,
        ...     print fileInArchive.comment,
        ...     print fileInArchive.datetime,
        ...     print time.strftime('%a, %d %b %Y %H:%M:%S', fileInArchive.datetime)
        test True 0 None (2003, 6, 30, 1, 59, 48, 0, 181, 1) Mon, 30 Jun 2003 01:59:48
        test.txt False 20 None (2003, 6, 30, 2, 1, 2, 0, 181, 1) Mon, 30 Jun 2003 02:01:02
        this.py False 1030 None (2002, 2, 8, 16, 47, 48, 4, 39, 0) Fri, 08 Feb 2002 16:47:48
        """
        index = 0
        headerData = RARHeaderDataEx()
        while not RARReadHeaderEx(self._handle, ctypes.byref(headerData)):
            rarFile = RarInfo(self, headerData, index)
            self.needskip = True
            yield rarFile
            index += 1
            if self.needskip:
                RARProcessFile(self._handle, RAR_SKIP, None, None)

    def infolist(self):
        """Return a list of RarInfos, descripting the contents of the archive."""
        return list(self.infoiter)

    def read_files(self, condition='*'):
        """Read specific files from archive into memory.
        If "condition" is a list of numbers, then return files which have those positions in infolist.
        If "condition" is a string, then it is treated as a wildcard for names of files to extract.
        If "condition" is a function, it is treated as a callback function, which accepts a RarInfo object and returns boolean True (extract) or False (skip).
        If "condition" is omitted, all files are returned.
        
        Returns list of tuples (RarInfo info, str contents)
        """
        res = []
        checker = condition2checker(condition)
        for info in self.infoiter():
            if checker(info) and not info.isdir:
                reader = PassiveReader()
                c_callback = UNRARCALLBACK(reader._callback)
                RARSetCallback(self._handle, c_callback, 1)
                RARProcessFile(self._handle, RAR_TEST, None, None)
                self.needskip = False
                res.append((info, reader.get_result()))
        return res
        

    def extract(self,  condition='*'):
        """Extract specific files from archive to disk.
        If "condition" is a list of numbers, then extract files which have those positions in infolist.
        If "condition" is a string, then it is treated as a wildcard for names of files to extract.
        If "condition" is a function, it is treated as a callback function, which accepts a RarInfo object and returns either boolean True (extract), boolean False (skip) or string - a new name to save the file under.
        If "condition" is omitted, all files are extracted.
        
        Returns list of RarInfos for extracted files."""
        res = []
        checker = condition2checker(condition)
        for info in self.infoiter():
            checkres = checker(info)
            if checkres!=False and not info.isdir:
                if checkres==True:
                    checkres = info.filename
                RARProcessFile(self._handle, RAR_EXTRACT, None, checkres)                
                self.needskip = False
                res.append(info)
        return res

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
