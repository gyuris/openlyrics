#! /usr/bin/env /usr/bin/python
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#  
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from datetime import datetime
from xml.etree import cElementTree as etree

u"""
Provides a module to access OpenLyrics data type.

Usage:
from openlyrics import Song
s = Song('song.xml')
"""

# A few 

def fromstring(text):
    u"Read from a string."
    tree = etree.fromstring(text)
    song = Song()
    if tree:
        song._from_xml(tree)
    return song

def tostring(song):
    u"Convert to a file."
    tree = song._to_xml()
    return etree.tostring(tree.getroot(), encoding=u'UTF-8')

def parse(filename):
    u"Read from the file."
    tree = etree.parse(filename)
    song = Song(tree)
    return song

class Song(object):
    u"""
    Definition of an song.
    
    titles:        A list of Title (class) objects.
    authors:       A list of Author (class) objects.
    songbooks:     A list of Songbook (class) objects, with a name and entry.
    themes:        A list of Theme (class) objects.
    comments:       A list of string comments
    """
    
    def __init__(self, filename=None):
        u"Create the instance."
        self.__ns = u''
        self._version = u'0.7'
        
        self.verses = []
        self.props = Properties()
        
        self.createdIn = u''
        self.modifiedIn = u''
        self.modifiedDate = u''

        if filename:
            self.parse(filename)
    
    def parse(self, filename):
        u"Read from the file."
        tree = etree.parse(filename)
        self._from_xml(tree)
    
    def write(self, filename):
        u"Save to a file."
        tree = self._to_xml()
        # lxml implements pretty printing
        # argument 'encoding' adds xml declaration:
        # <?xml version='1.0' encoding='UTF-8'?>
        try:
            tree.write(filename, encoding=u'UTF-8', pretty_print=True)
        except TypeError:
            # TODO: implement pretty_print for other ElementTree API
            # implementations
            tree.write(filename, encoding=u'UTF-8')
    
    def _from_xml(self, tree):
        u"Read from XML."
        if isinstance(tree, etree.ElementTree):
            root = tree.getroot()
        else:
            root = tree
        
        if u'}' in root.tag:
            self.__ns = root.tag.split(u'}')[0].lstrip(u'{')
        self.createdIn = root.get(u'createdIn', u'')
        self.modifiedIn = root.get(u'modifiedIn', u'')
        self.modifiedDate = root.get(u'modifiedDate', u'')
        
        self.props._from_xml(tree, self.__ns)
        
        self.verses = []
        for verse_elem in tree.findall(_path(u'lyrics/verse',self.__ns)):
            verse = Verse()
            verse._from_xml(verse_elem, self.__ns)
            self.verses.append(verse)
    
    def _to_xml(self):
        u"Convert to XML."
        root = etree.Element(u'song')
        root.set(u'xmlns', self.__ns)
        root.set(u'version', self._version)
        root.set(u'createdIn', self.createdIn)
        root.set(u'modifiedIn', self.modifiedIn)
        root.set(u'modifiedDate', datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
        
        props = self.props._to_xml()
        root.append(props)
        
        verses_elem = etree.Element(u'verses')
        for verse in self.verses:
            verses_elem.append(verse._to_xml())
        root.append(verses_elem)
        
        #TODO: Verses
        
        tree = etree.ElementTree(root)
        return tree
    

class Properties(object):
    u"""
    Stores Song property elements.
    
    release_date:   The date, in the format of yyyy-mm-ddThh:mm.
    ccli_no:        The CCLI number. Numeric or string value.
    tempo:          Numeric value of speed.
    tempo_type:     Unit of measurement of tempo. Example: "bpm".
    key:            Key of a string. Example: "Eb".
    transposition:  Key adjustment up or down. Integer value.
    verse_order:    The verse names in a specific order.
    variant:        A string describing differentiating it from other songs
                    with a common title.
    keywords:       
    copyright:      A copyright string.
    publisher:      A string value of the song publisher.
    custom_version: 
    """
    def __init__(self):
        # List types
        self.titles = []
        self.authors = []
        self.songbooks = []
        self.themes = []
        self.comments = []
        
        # String Types
        self.release_date = u''
        self.ccli_no = u''
        self.tempo = u''
        self.tempo_type = u''
        self.key = u''
        self.transposition = u'0'
        self.verse_order = u''
        self.variant = u''
        self.keywords = u'' # Should keywords be a list?
        self.copyright = u''
        self.publisher = u''
        self.custom_version = u''
        
    def _from_xml(self, tree, namespace):
        u""
        self.titles = []
        elem = tree.findall(_path(u'properties/titles/title',namespace))
        for el in elem:
            title = Title(el.text, el.get(u'lang',None))
            self.titles.append(title)
        
        self.authors = []
        elem = tree.findall(_path(u'properties/authors/author',namespace))
        for el in elem:
            author = Author(el.text, el.get(u'type',None),
                            el.get(u'lang',None))
            self.authors.append(author)
        
        self.songbooks = []
        elem = tree.findall(_path(u'properties/songbooks/songbook',namespace))
        for el in elem:
            songbook = Songbook(el.get(u'name',None), el.get(u'entry',None))
            self.songbooks.append(songbook)
        
        self.themes = []
        elem = tree.findall(_path(u'properties/themes/theme',namespace))
        for el in elem:
            theme = Theme(el.text, el.get(u'id',None), el.get(u'lang',None))
            self.themes.append(theme)
        
        self.comments = []
        elem = tree.findall(_path(u'properties/comments/comment',namespace))
        for el in elem:
            self.comments.append(el.text)
        
        elem = tree.find(_path(u'properties/copyright',namespace))
        if elem != None:
            self.copyright = elem.text
        
        elem = tree.find(_path(u'properties/ccliNo',namespace))
        if elem != None:
            self.ccli_no = elem.text
        
        elem = tree.find(_path(u'properties/releaseDate',namespace))
        if elem != None:
            self.release_date = elem.text
        
        elem = tree.find(_path(u'properties/tempo',namespace))
        if elem != None:
            self.tempo_type = elem.get(u'type',None)
            self.tempo = elem.text
        
        elem = tree.find(_path(u'properties/key',namespace))
        if elem != None:
            self.key = elem.text
        
        elem = tree.find(_path(u'properties/verseOrder',namespace))
        if elem != None:
            self.verse_order = elem.text
        
        elem = tree.find(_path(u'properties/keywords',namespace))
        if elem != None:
            self.keywords = elem.text
        
        elem = tree.find(_path(u'properties/transposition',namespace))
        if elem != None:
            self.transposition = elem.text
        
        elem = tree.find(_path(u'properties/variant',namespace))
        if elem != None:
            self.variant = elem.text
        
        elem = tree.find(_path(u'properties/publisher',namespace))
        if elem != None:
            self.publisher = elem.text
        
        elem = tree.find(_path(u'properties/customVersion',namespace))
        if elem != None:
            self.custom_version = elem.text
    
    def _to_xml(self):
        u""
        props = etree.Element(u'properties')
        
        if len(self.titles):
            elem1 = etree.Element(u'titles')
            for t in self.titles:
                elem1.append(t._to_xml())
            props.append(elem1)
        
        if len(self.authors):
            elem1 = etree.Element(u'authors')
            for a in self.authors:
                elem1.append(a._to_xml())
            props.append(elem1)
        
        if len(self.songbooks):
            elem1 = etree.Element(u'songbooks')
            for s in self.songbooks:
                elem1.append(s._to_xml())
            props.append(elem1)
        
        if len(self.themes):
            elem1 = etree.Element(u'themes')
            for t in self.themes:
                elem1.append(t._to_xml())
            props.append(elem1)
        
        if len(self.comments):
            elem1 = etree.Element(u'comments')
            for c in self.comments:
                elem2 = etree.Element(u'comment')
                elem2.text = str(c)
                elem1.append(elem2)
            props.append(elem1)
        
        if self.copyright:
            elem1 = etree.Element(u'copyright')
            elem1.text = str(self.copyright)
            props.append(elem1)
        
        if self.ccli_no:
            elem1 = etree.Element(u'ccliNo')
            elem1.text = str(self.ccli_no)
            props.append(elem1)
        
        if self.release_date:
            elem1 = etree.Element(u'releaseDate')
            elem1.text = str(self.release_date)
            props.append(elem1)
        
        if self.tempo:
            elem1 = etree.Element(u'tempo')
            if self.tempo_type:
                elem1.set(u'type',self.tempo_type)
            elem1.text = self.tempo
            props.append(elem1)
        
        if self.key:
            elem1 = etree.Element(u'key')
            elem1.text = self.key
            props.append(elem1)
        
        if self.verse_order:
            elem1 = etree.Element(u'verseOrder')
            elem1.text = self.verse_order
            props.append(elem1)
        
        if self.keywords:
            elem1 = etree.Element(u'keywords')
            elem1.text = self.keywords
            props.append(elem1)
        
        if self.transposition:
            elem1 = etree.Element(u'transposition')
            elem1.text = self.transposition
            props.append(elem1)
        
        if self.variant:
            elem1 = etree.Element(u'variant')
            elem1.text = self.variant
            props.append(elem1)
        
        if self.publisher:
            elem1 = etree.Element(u'publisher')
            elem1.text = self.publisher
            props.append(elem1)
        
        if self.custom_version:
            elem1 = etree.Element(u'customVersion')
            elem1.text = self.custom_version
            props.append(elem1)
        
        return props
    

class Title(object):
    u"""
    A title for the song.
    
    title: The title as a string.
    lang:  A language code, in the format of "xx", or "xx-YY".
    """
    
    def __init__(self, title=u'', lang=None):
        u"Create the instance."
        self.title = title
        self.lang = lang
    
    def _to_xml(self):
        u"Create the XML element."
        elem = etree.Element(u'title')
        if self.lang:
            elem.set(u'lang', self.lang)
        elem.text = self.title
        return elem
    
    def __str__(self):
        u"Return a string representation."
        return self.title
    
    def __unicode__(self):
        u"Return a unicode representation."
        return self.title


class Author(object):
    u"""
    An author of words, music, or a translation.
    
    author: Author's name as a string.
    type:   One of "words", "music", or "translation". This module will throw
            ValueError if one of these is found to be incorrect.
    lang:   A language code, in the format of "xx", or "xx-YY".
    """
    
    def __init__(self, author=u'', type_=None, lang=None):
        u"Create the instance. May return `ValueError`."
        self.author = author
        if type_ and type_ not in (u'words',u'music',u'translation'):
            raise ValueError(u'`type` must be one of "words", "music", or' +
                    '"translator".')
        self.type = type_
        self.lang = lang
    
    def _to_xml(self):
        elem = etree.Element(u'author')
        if self.type:
            elem.set(u'type',self.type)
            if self.type == u'translator' and self.lang:
                elem.set(u'lang',self.lang)
        elem.text = self.author
        return elem
    
    def __str__(self):
        u"Return a string representation."
        return self.author
    
    def __unicode__(self):
        u"Return a unicode representation."
        return self.author


class Songbook(object):
    u"""
    A songbook/collection with an entry/number.
    
    name:  The name of the songbook or collection.
    entry: A number or string representing the index in this songbook.
    """
    
    def __init__(self, name=u'', entry=None):
        u"Create the instance."
        self.name = name
        self.entry = entry
    
    def _to_xml(self):
        u"Create the XML element."
        elem = etree.Element(u'songbook')
        if self.entry:
            elem.set(u'entry',self.entry)
        elem.text = self.name
        return elem
    
    def __str__(self):
        u"Return a string representation."
        return u'%s #%s' % (self.name, self.entry)
    
    def __unicode__(self):
        u"Return a unicode representation."
        return u'%s #%s' % (self.name, self.entry)


class Theme(object):
    u"""
    A category for the song.
    
    theme: The name of the song.
    id:    A number from the standardized CCLI list.
                 http://www.ccli.com.au/owners/themes.cfm
    lang:  A language code, in the format of "xx", or "xx-YY".
    """
    
    def __init__(self, theme=u'', id=None, lang=None):
        u"Create the instance."
        self.theme = theme
        self.id = id
        self.lang = lang
    
    def _to_xml(self):
        elem = etree.Element(u'theme')
        if self.id:
            elem.set(u'id',self.id)
        if self.lang:
            elem.set(u'lang',self.lang)
        elem.text = self.theme
        return elem
    
    def __str__(self):
        u"Return a string representation."
        return self.theme
    
    def __unicode__(self):
        u"Return a unicode representation."
        return self.theme

    
# Verse element and subelements

class Verse(object):
    u"""
    A verse for a song.
    """
    
    def __init__(self):
        u"Create the instance."
        self.lang = None
        self.translit = None
        self.name = None
        self.lines = []
    
    def _from_xml(self, tree, namespace):
        self.name = tree.get(u'name', None)
        self.lang = tree.get(u'lang', None)
        self.translit = tree.get(u'translit', None)
        for lines_elem in tree.findall(_path(u'lines', namespace)):
            lines = Lines()
            lines._from_xml(lines_elem, namespace)
            self.lines.append(lines)
    
    def _to_xml(self):
        u""
        verse = etree.Element('verse')
        if self.name:
            verse.set(u'name', self.name)
        if self.lang:
            verse.set(u'lang', self.lang)
        if self.translit:
            verse.set(u'translit', self.translit)
        for lines in self.lines:
            verse.append(lines._to_xml())
        return verse
    

class Lines(object):
    u"""
    A group of lines in a verse.
    """
    
    def __init__(self):
        u"Create the instance."
        self.lines = []
        self.part = None
    
    def _from_xml(self, elem, namespace):
        u""
        self.part = elem.get(u'part', None)
        for line_elem in elem.findall(_path(u'line', namespace)):
            # TODO: This returns the outer element, but it should not.
            
            self.lines.append( Line(line_elem) )
    
    def _to_xml(self):
        u""
        lines_elem = etree.Element('lines')
        if self.part:
            lines_elem.set('part', self.part)
        for line in self.lines:
            line_elem = etree.fromstring(u'<line>%s</line>' % line.markup)
            lines_elem.append(line_elem)
        return lines_elem
    
    def __str__(self):
        u"Return a string representation."
        return u'\n'.join(str(l) for l in self.lines)
    
    def __unicode__(self):
        u"Return a unicode representation."
        return u'\n'.join(unicode(l) for l in self.lines)

class Line(object):
    u"""
    A single line in a group of lines.
    """
    __chords_regex = re.compile(u'<chord[^>]>')
    
    def __init__(self, elem):
        self.markup = _element_contents_to_string(elem)
    
    def _get_text(self):
        u"Get the text for this line."
        return self.__chords_regex.sub(u'',self.markup)
    
    def _set_text(self, value):
        u"Set the text for this line. This removes all chords."
        self.markup = value
    
    text = property(_get_text, _set_text)
    
    def _get_chords(self):
        u"Get the chords for this line."
        self.__chords_regex.findall(self.markup)
    
    chords = property(_get_chords)
    
    def __str__(self):
        u"Return a string representation."
        return str(self.text)
    
    def __unicode__(self):
        u"Return a unicode representation."
        return self.text


# Various functions

def _path(tag, ns=None):
    u"""
    If a namespace is on a document, the XPath requires {ns}tag for every
    tag in the path. This assumes that only one namespace for the document
    exists.
    """
    if ns == None or len(ns) == 0:
        return tag
    else:
        return u'/'.join(u'{%s}%s' % (ns, t) for t in tag.split(u'/'))

def _element_contents_to_string(elem):
    u"Function that returns the a string representation."
    s = u""
    if elem.text:
        s += elem.text
    if s == None:
        s = u""
    for sub in elem.getchildren():
        # Strip the namespace
        if sub.tag.partition("}")[2]:
            tag = sub.tag.partition("}")[2]
        else:
            tag = sub.tag
        subtag = " ".join((tag,) + tuple('%s="%s"' % i for i in sub.items()))
        subtext = _element_contents_to_string(sub)
        if subtext:
            s += "<%(tag)s>%(text)s</%(tag)s>" % \
                    {"tag": subtag, "text": subtext}
        else:
            s += "<%(tag)s />" % {"tag": subtag}
        if sub.tail:
            s += sub.tail
    return unicode(s)