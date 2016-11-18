import gflags
import sys
import logging
from xml.dom import minidom
import os
from os import path
import re
import codecs

from bibtexparser.bparser import BibTexParser

gflags.DEFINE_string('mindmap_file', None, 'the mindmap filename')
gflags.DEFINE_boolean('use_absolute_paths_for_images', False,
                      'when set, will use absolute paths for images')
gflags.DEFINE_string('html_file', None, 'the html filename')
gflags.DEFINE_string('latex_file', None, 'the latex filename')
gflags.DEFINE_string('beamer_latex_file', None, 'the beamer latex filename')
gflags.DEFINE_string('bib_file', '~/Dropbox/bib.bib',
                     'bib file location')


class BibDatabase(object):

  def __init__(self, bib_file_location=None):
    if bib_file_location is None:
      bib_file_location = gflags.FLAGS.bib_file
    bib_file_location = re.sub('~', os.environ['HOME'], bib_file_location)
    with open(bib_file_location) as bibfile:
      content = bibfile.read()
      bp = BibTexParser(content)
    self.entry_map = {}
    for ent in bp.get_entry_list():
      self.entry_map[ent['id']] = ent

  def _RetrieveEntry(self, name):
    return self.entry_map[name]

  db = None

  @staticmethod
  def GetTheDB():
    if BibDatabase.db is None:
      BibDatabase.db = BibDatabase()
    return BibDatabase.db

  def GetFormattedAuthor(self, bib_authorname):
    names = bib_authorname.split(' and ')
    first_author_lastname = names[0].split(',')[0]
    if len(names) == 1:
      return first_author_lastname
    elif len(names) >= 3:
      return "%s et. al. " % first_author_lastname
    else:
      second_author_lastname = names[1].split(',')[0]
      return "%s and %s" % (first_author_lastname,
                            second_author_lastname)

  def GetOneArtCiteHTML(self, name):
    try:
      ent = self._RetrieveEntry(name)
    except:
      return "InvalidBibEntry:%s" % name
    return "<span class=\"citation\" title=\"%s\">%s, %s</span>" % (
      ent["title"],
      self.GetFormattedAuthor(ent['author']),
      ent['year'])

  def GetOneArtNewciteHTML(self, name):
    try:
      ent = self._RetrieveEntry(name)
    except:
      return "InvalidBibEntry:%s" % name
    return "<span class=\"citation\" title=\"%s\">%s (%s)</span>" % (
      ent["title"],
      self.GetFormattedAuthor(ent['author']),
      ent['year'])

  def GetCiteHTML(self, name):
    return '(%s)' % (
      "; ".join(self.GetOneArtCiteHTML(x) for x in name.split(',')))

  def GetNewciteHTML(self, name):
    return ", ".join(self.GetOneArtNewciteHTML(x) for x in name.split(','))


class Node(object):
  accepted_nodes = ['node', 'richcontent']

  def __init__(self, dom_node, level=0):
    self.type = dom_node.nodeName
    self.level = level

    try:
      self.nodeid = dom_node.attributes['ID'].value
    except:
      self.nodeid = "NONE"

    try:
      self.text = dom_node.attributes['TEXT'].value
    except:
      self.text = "NONE"

    self.printing_func = None

    self.children = []
    for child in dom_node.childNodes:
      self.AddInfoForChild(child)

  def AddInfoForChild(self, child):
    if child.nodeType == child.TEXT_NODE:
      return
    if child.nodeName not in Node.accepted_nodes:
      return

    if child.nodeName == 'richcontent':
      self.children.append(ImageNode(child, self.level + 1))
      return

    if 'TEXT' not in child.attributes.keys():
      for g in child.childNodes:
        self.AddInfoForChild(g)
      return

    if child.attributes['TEXT'].value.startswith('#'):
      return

    self.children.append(Node(child, self.level + 1))

  def __str__(self):
    pass

  def GetText(self, format='html'):
    def ReplaceCitations(s):
      def get_cite_html(mo):
        citation = BibDatabase.GetTheDB().GetCiteHTML(mo.group(1))
        return citation

      def get_newcite_html(mo):
        citation = BibDatabase.GetTheDB().GetNewciteHTML(mo.group(1))
        return citation

      s = re.sub(
        r'\\cite{(.*?)}',
        get_cite_html,
        s)
      s = re.sub(
        r'\\newcite{(.*?)}',
        get_newcite_html,
        s)
      return s

    def ReplaceEmphMarkups(s):
      return re.sub(
        r'\\emph{(.*?)}',
        lambda x: '<i>%s</i>' % x.group(1),
        s)

    def ReplaceSubScores(s):
      return re.sub(
        r'\_',
        '_',
        s)

    def ReplacePercScores(s):
      return re.sub(
        r'\%',
        '%',
        s)

    def ReplaceTextBFMarkups(s):
      return re.sub(
        r'\\textbf{(.*?)}',
        lambda x: '<b>%s</b>' % x.group(1),
        s)

    def ReplaceFootnoteMarkups(s):
      return re.sub(
        r'\\footnote{(.*)}',
        lambda x: '<span title="%s" class="footnote">FOOTNOTE</span>' % x.group(
          1),
        s)

    def ReplaceUnderlineMarkups(s):
      return re.sub(
        r'\\underline{(.*?)}',
        lambda x: '<u>%s</u>' % x.group(1),
        s)

    def ReplaceTextSFMarkups(s):
      return re.sub(
        r'\\textsf{(.*?)}',
        lambda x: '<span class="sf">%s</span>' % x.group(1),
        s)

    def ReplaceSoutMarkups(s):
      return re.sub(
        r'\\sout{(.*?)}',
        lambda x: '<strike>%s</strike>' % x.group(1),
        s)

    def ReplaceTildas(s):
      return s.replace('~', ' ')

    def ReplaceLdots(s):
      return s.replace('\\ldots', '...')

    def ReplaceDollarSigns(s):
      s1 = re.sub(r'\$\$(.*?)\$\$', lambda mo: r"\[%s\]" % mo.group(1), s)
      s2 = re.sub(r'\$(.*?)\$', lambda mo: r"\(%s\)" % mo.group(1), s1)
      return s2

    filters = [ReplaceTildas,
               ReplacePercScores,
               ReplaceTextBFMarkups,
               ReplaceEmphMarkups,
               ReplaceTextSFMarkups,
               ReplaceSoutMarkups,
               ReplaceUnderlineMarkups,
               ReplaceCitations,
               ReplaceLdots,
               ReplaceDollarSigns,
               ReplaceSubScores,
               ReplaceFootnoteMarkups,
               ]

    txt = self.text
    if format == 'beamer_latex':
      format = 'latex'
    if format == 'latex':
      if '<TABLE' in txt or '<table' in txt:
        return "TABLE"
      return txt
    for f in reversed(filters):
      txt = f(txt)
    return txt

  def PrintSelfToWriter(self, writer, format='html'):
    if self.level == 0:
      return

    writer.write(self.GetText(format))

  def SetPrintingFunc(self, func):
    self.printing_func = func

  def GetChildren(self):
    return self.children

  def GetPrintableChildren(self):
    return [child for child in self.GetChildren() if child.IsPrintable()]

  def HasPrinter(self):
    return (self.printing_func is not None)

  def GetPrinter(self):
    assert self.printing_func is not None
    return self.printing_func

  def GetLevel(self):
    return self.level

  def IsFormattingNode(self):
    return (self.GetText() in ['SECTIONS', 'SUBSECTIONS', 'SUBSUBSECTIONS',
                               'LIST', 'ULIST', 'HLIST']) or self.GetText().startswith('WIDTH=')

  def GetTheFormattingChildNode(self):
    for child in self.GetChildren():
      if child.IsFormattingNode():
        return child
    return None

  def IsImageNode(self):
    return False

  def IsCommentNode(self):
    return self.GetText().startswith('Comment:')

  def IsStoryNode(self):
    return self.GetText().startswith('Story:')

  def IsPrintable(self):
    return (not self.IsFormattingNode())

  def IsGraphNodeDescription(self):
    cld = self.GetPrintableChildren()
    return ((len(cld) == 1) and (cld[0].IsImageNode()))

  def IsHelperNode(self):
    return self.IsStoryNode() or self.IsCommentNode()

  def IsLeafNode(self):
    formatting_node = self.GetTheFormattingChildNode()
    if formatting_node is not None and (
        formatting_node.GetText() == 'LIST'
        or formatting_node.GetText() == 'ULIST'
        or formatting_node.GetText() == 'HLIST'
    ):
      return True
    return len(self.GetPrintableChildren()) == 0 or self.IsGraphNodeDescription(
    ) or all(child.IsHelperNode() for child in self.GetPrintableChildren())

  def QualifyAsParagraph(self):
    cld = self.GetPrintableChildren()
    return not self.IsLeafNode() and all(child.IsLeafNode()
                                         for child in cld) and not self.IsGraphNodeDescription()


class ImageNode(Node):

  def __init__(self, dom_node, level):
    Node.__init__(self, dom_node, level)
    rel_loc = dom_node.getElementsByTagName("img")[0].attributes['src'].value
    loc = rel_loc
    if gflags.FLAGS.use_absolute_paths_for_images:
      loc = path.abspath(path.join(
        path.dirname(gflags.FLAGS.mindmap_file), rel_loc))
    self.img = loc

  def IsImageNode(self):
    return True

  def GetImageLoc(self):
    return self.img

  def IsLeafNode(self):
    return True


def GetPrinterFromFormattingNode(formatting_node, node):
  fn_text = formatting_node.GetText()
  mo = re.match(r'WIDTH=(\d+(\.\d+))', fn_text)
  if mo is not None:
    return OutputImage(node, width=float(mo.group(1)))

  tags_map = {'SECTIONS': PrintCurrentAsSection(node, 'h2'),
              'SUBSECTIONS': PrintCurrentAsSection(node, 'h3'),
              'SUBSUBSECTIONS': PrintCurrentAsSection(node, 'h4'),
              }
  return tags_map[fn_text]


class Organization(object):

  def __init__(self, mm_file_content):
    dom = minidom.parseString(mm_file_content)
    self.doc = self.SaveFromDom(dom)
    self.LabelTree(self.doc)

  def SaveFromDom(self, dom):
    return Node(dom.childNodes[0])

  def _TraverseAllDescendents(self, node=None):
    """An iterator to yield all the descendents in a DFS manner

    Args:
      node: the current node. When it is none, will start from the root.

    Returns:
      An iterator of all descendents, including itself.
    """
    if node is None:
      node = self.doc
    yield node
    for child in node.children:
      for grand_kid in self._TraverseAllDescendents(child):
        yield grand_kid

  def LabelAllIntoLayers(self, node):
    formatting_node = node.GetTheFormattingChildNode()
    if formatting_node is not None:
      if formatting_node.GetText() == 'LIST':
        node.SetPrintingFunc(OutputOrderedList(node))
        for child in node.GetChildren():
          self.LabelAllIntoLayers(child)
        return
      if formatting_node.GetText() == 'ULIST':
        node.SetPrintingFunc(OutputUnorderedList(node))
        for child in node.GetChildren():
          self.LabelAllIntoLayers(child)
        return
      if formatting_node.GetText() == 'HLIST':
        node.SetPrintingFunc(OutputHAlignedList(node))
        for child in node.GetChildren():
          self.LabelAllIntoLayers(child)
        return
      if not node.HasPrinter():
        node.SetPrintingFunc(DirectlyPrintThisAndSub(node))
      for child in node.GetPrintableChildren():
        child.SetPrintingFunc(
          GetPrinterFromFormattingNode(formatting_node, child))

    if node.GetLevel() == 1:
      node.SetPrintingFunc(PrintTopLevel(node))

    if node.IsCommentNode():
      node.SetPrintingFunc(OutputComment(node))
    elif node.IsStoryNode():
      node.SetPrintingFunc(OutputStory(node))
    elif node.IsGraphNodeDescription():
      node.SetPrintingFunc(DirectlyPrintThisAndSub(node))

    if not node.HasPrinter():
      if node.IsImageNode():
        node.SetPrintingFunc(OutputImage(node))
      elif node.QualifyAsParagraph():
        node.SetPrintingFunc(OutputParagraph(node))
      else:
        node.SetPrintingFunc(OutputOrderedList(node))

    for child in node.GetChildren():
      self.LabelAllIntoLayers(child)

  def LabelTree(self, node):
    self.LabelAllIntoLayers(node)
    node.SetPrintingFunc(DirectlyPrintSub(node))

  def LabelErrorsOnFrames(self, node_error_mapping):
    """Label frames in the graph to output error messages instead.

    It will label the frame in a way to print its contents as they are,
    with the error message on the title.

    Args:
      node_error_mapping: mappings between frames' corresponding
        node IDs and the error they produce.
    """
    for node in self._TraverseAllDescendents():
      if node.nodeid in node_error_mapping:
        node.SetPrintingFunc(
          OutputFrameAndDebugMessage(
            node, node_error_mapping[node.nodeid]))

  def OutputToHTML(self, filename):
    with codecs.open(filename, 'w', 'utf8') as outputfile:
      print >> outputfile, """
<meta charset="UTF-8">
<style>
span.citation {
   color : blue;
}
span.footnote {
   color : green;
   font-size: 50%;
   vertical-align: top;
}
span.sf {
  font-family: "Arial Black", Gadget, sans-serif
}
</style>
<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
<script language="javascript">
var should_hide = false;

 window.onload = function() {
   should_hide = true;
   SetVisability();
 }

 function SetVisability() {
  var cols = document.getElementsByClassName('help');
  for(i=0; i<cols.length; i++) {
    cols[i].hidden = should_hide;
  }
 }

function ToggleComments() {
  should_hide = !should_hide;
  SetVisability();
}
</script>
<button onclick="ToggleComments()">show/hide comments</button>
            """

      self.doc.GetPrinter()(outputfile)

  def OutputToLatex(self, filename):
    with codecs.open(filename, 'w', 'utf8') as outputfile:
      self.doc.GetPrinter()(outputfile, 'latex')

  def OutputToBeamerLatex(self, filename):
    with codecs.open(filename, 'w', 'utf8') as outputfile:
      self.doc.GetPrinter()(outputfile, 'beamer_latex')


def OutputOrderedList(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    PrintInLatexFormatWithTag(writer, 'beamer_latex')

  def PrintInHTMLFormat(writer):
    current_node.PrintSelfToWriter(writer)
    if len(current_node.GetPrintableChildren()) > 0:
      writer.write('<ol>')
      for t in current_node.GetPrintableChildren():
        if t.IsStoryNode() or t.IsCommentNode():
          t.GetPrinter()(writer)
          writer.write('<br>')
        else:
          writer.write('<li>')
          t.GetPrinter()(writer)
          writer.write('</li>')
      writer.write('</ol>')

  def PrintInLatexFormat(writer):
    PrintInLatexFormatWithTag(writer, 'latex')

  def PrintInLatexFormatWithTag(writer, tag='latex'):
    current_node.PrintSelfToWriter(writer, tag)
    if len(current_node.GetPrintableChildren()) > 0:
      writer.write(r'\begin{enumerate}')
      for t in current_node.GetPrintableChildren():
        if t.IsStoryNode() or t.IsCommentNode():
          t.GetPrinter()(writer, tag)
          writer.write('\n')
        else:
          writer.write(r'\item ')
          t.GetPrinter()(writer, tag)
          writer.write('\n')
      writer.write(r'\end{enumerate}')

  return PrintTo


def OutputUnorderedList(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    PrintInLatexFormatWithFormatTag(writer, 'beamer_latex')

  def PrintInHTMLFormat(writer):
    current_node.PrintSelfToWriter(writer)
    if len(current_node.GetPrintableChildren()) > 0:
      writer.write('<ul>')
      for t in current_node.GetPrintableChildren():
        if t.IsStoryNode() or t.IsCommentNode():
          t.GetPrinter()(writer)
          writer.write('<br>')
        else:
          writer.write('<li>')
          t.GetPrinter()(writer)
          writer.write('</li>')
      writer.write('</ul>')

  def PrintInLatexFormat(writer):
    PrintInLatexFormatWithFormatTag(writer, 'latex')

  def PrintInLatexFormatWithFormatTag(writer, tag='latex'):
    current_node.PrintSelfToWriter(writer, tag)
    if len(current_node.GetPrintableChildren()) > 0:
      writer.write(r'\begin{itemize}')
      for t in current_node.GetPrintableChildren():
        if t.IsStoryNode() or t.IsCommentNode():
          t.GetPrinter()(writer, tag)
          writer.write('\n')
        else:
          writer.write(r'\item ')
          t.GetPrinter()(writer, tag)
          writer.write('\n')
      writer.write(r'\end{itemize}')

  return PrintTo


def OutputHAlignedList(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    PrintInLatexFormatWithFormatTag(writer, 'beamer_latex')

  def PrintInHTMLFormat(writer):
    current_node.PrintSelfToWriter(writer)
    if len(current_node.GetPrintableChildren()) > 0:
      writer.write('<ul>')
      for t in current_node.GetPrintableChildren():
        if t.IsStoryNode() or t.IsCommentNode():
          t.GetPrinter()(writer)
          writer.write('<br>')
        else:
          writer.write('<li>')
          t.GetPrinter()(writer)
          writer.write('</li>')
      writer.write('</ul>')

  def PrintInLatexFormat(writer):
    PrintInLatexFormatWithFormatTag(writer, 'latex')

  def PrintInLatexFormatWithFormatTag(writer, tag='latex'):
    current_node.PrintSelfToWriter(writer, tag)
    if len(current_node.GetPrintableChildren()) > 0:
      all_children = current_node.GetPrintableChildren()
      algned_children = [t for t in all_children if not (
        t.IsStoryNode() or t.IsCommentNode())]
      n = len(algned_children)
      writer.write(r'\vspace{0.2cm}\begin{columns}[onlytextwidth]')
      col_width = 0.9 / n
      for t in all_children:
        if t.IsStoryNode() or t.IsCommentNode():
          t.GetPrinter()(writer, tag)
          writer.write('\n')
        else:
          writer.write(
            r'\begin{column}{%.2f\textwidth} \centering ' %
            col_width)
          t.GetPrinter()(writer, tag)
          writer.write(r'\end{column}')
      writer.write(r'\end{columns}')

  return PrintTo


def OutputStory(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    pass

  def PrintInHTMLFormat(writer):
    writer.write('<i><span class="help">')
    current_node.PrintSelfToWriter(writer)
    writer.write('</span></i>')

  def PrintInLatexFormat(writer):
    writer.write('%%')
    current_node.PrintSelfToWriter(writer, 'latex')

  return PrintTo


def OutputImage(current_node, width=None):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer, current_node, width)
    elif format == 'latex':
      PrintInLatexFormat(writer, current_node, width)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer, current_node, width)

  def PrintInBeamerLatexFormat(writer, current_node, width):
    if width is None:
      width = r'.7\textwidth'
    elif width <= 1:
      width = r'%.2f\textwidth' % width
    else:
      width = r'%.2fpx' % width

    writer.write(r'\begin{centering}\includegraphics[width=%s]{%s}' % (
      width, current_node.GetImageLoc()))
    writer.write(r'\end{centering}')

  def PrintInHTMLFormat(writer, current_node, width):
    if width is None:
      width = 500
    writer.write(
      '<center><img src="%s" width="%.2fpx">' %
      (current_node.GetImageLoc(), width))
    writer.write('</img></center>')

  def PrintInLatexFormat(writer, current_node, width):
    if width is None:
      width = r'.7\textwidth'
    else:
      width = r'%.2f\textwidth' % width

    writer.write(r'\begin{figure}\includegraphics[width=%s]{%s}' % (
      width, current_node.GetImageLoc()))
    writer.write(r'\end{figure}')

  return PrintTo


def OutputComment(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    PrintInLatexFormat(writer)

  def PrintInHTMLFormat(writer):
    writer.write('<span class="help" style="color:red">')
    current_node.PrintSelfToWriter(writer)
    writer.write('</span>')

  def PrintInLatexFormat(writer):
    writer.write(r'\todo[size=\tiny]{')
    current_node.PrintSelfToWriter(writer, 'latex')
    writer.write(r'}')

  return PrintTo


def OutputParagraph(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    writer.write("\n%%frame: {}%%\n".format(current_node.nodeid))
    writer.write(r'\begin{frame}{')
    current_node.PrintSelfToWriter(writer, 'beamer_latex')
    writer.write(r'}')
    for i in current_node.GetPrintableChildren():
      i.GetPrinter()(writer, 'beamer_latex')
      writer.write('\n')
    writer.write(r'\end{frame}')

  def PrintInHTMLFormat(writer):
    writer.write(
      '<p><span class="help" style="font-size:120%; font-style:italic">')
    current_node.PrintSelfToWriter(writer)
    writer.write('</span>')
    for i in current_node.GetPrintableChildren():
      writer.write('<br class="help"> ')
      i.GetPrinter()(writer)
    writer.write('</span></p>')

  def PrintInLatexFormat(writer):
    writer.write('\n%%')
    current_node.PrintSelfToWriter(writer, 'latex')
    writer.write('\n')
    for i in current_node.GetPrintableChildren():
      i.GetPrinter()(writer, 'latex')
      writer.write('\n')
    writer.write('\n')

  return PrintTo


def DirectlyPrintSub(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    for t in current_node.GetPrintableChildren():
      t.GetPrinter()(writer, 'beamer_latex')
      writer.write('\n')

  def PrintInHTMLFormat(writer):
    for t in current_node.GetPrintableChildren():
      t.GetPrinter()(writer)
      writer.write(' <br class="help">')

  def PrintInLatexFormat(writer):
    for t in current_node.GetPrintableChildren():
      t.GetPrinter()(writer, 'latex')
      writer.write('\n')

  return PrintTo


def OutputFrameAndDebugMessage(current_node, error_messages):
  """Output the error message as title, and normal content as content.

  This printer is used when there is an error on this page.

  Args:
    current_node: the current node (a frame).
    error_messages: a list of latex compilation messages for errors in this frame.

  Returns:
    A printer for printing the latex code into a writer.
  """

  def PrintTo(writer, format='beamer_latex'):
    if format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)
    else:
      logging.fatal("Unsupported format %s", format)

  def PrintInBeamerLatexFormat(writer):
    writer.write(r'\begin{frame}[fragile]{Error on page\ldots}')
    writer.write(r'\begin{verbatim}')
    writer.write('\n')
    for msg in error_messages:
      writer.write(msg)
      writer.write("\n")
    writer.write(r'\end{verbatim}')
    writer.write('\n')
    writer.write(r'\end{frame}')

  return PrintTo


def DirectlyPrintThisAndSub(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    writer.write(current_node.GetText(format='beamer_latex'))
    writer.write('\n')
    for t in current_node.GetPrintableChildren():
      t.GetPrinter()(writer, 'beamer_latex')
      writer.write('\n')

  def PrintInHTMLFormat(writer):
    writer.write(current_node.GetText())
    writer.write('<br>')
    for t in current_node.GetPrintableChildren():
      t.GetPrinter()(writer)
      writer.write('<br>')

  def PrintInLatexFormat(writer):
    writer.write(current_node.GetText(format='latex'))
    writer.write('\n')
    for t in current_node.GetPrintableChildren():
      t.GetPrinter()(writer, 'latex')
      writer.write('\n')

  return PrintTo


def PrintCurrentAsSection(current_node, tag):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    latex_tag = None
    if tag == 'h2':
      latex_tag = 'section'
    elif tag == 'h3':
      latex_tag = 'subsection'
    elif tag == 'h4':
      latex_tag = 'subsubsection'
    assert latex_tag is not None
    txt = current_node.GetText('latex')
    if len(txt.strip()) > 0:
      writer.write(r"\%s{" % latex_tag)
      writer.write(txt)
      writer.write("}\n")
    DirectlyPrintSub(current_node)(writer, 'beamer_latex')

  def PrintInHTMLFormat(writer):
    writer.write("<%s>" % tag)
    writer.write(current_node.GetText())
    writer.write("</%s>" % tag)
    DirectlyPrintSub(current_node)(writer)

  def PrintInLatexFormat(writer):
    latex_tag = None
    if tag == 'h2':
      latex_tag = 'section'
    elif tag == 'h3':
      latex_tag = 'subsection'
    elif tag == 'h4':
      latex_tag = 'subsubsection'
    assert latex_tag is not None
    txt = current_node.GetText('latex')
    if len(txt.strip()) > 0:
      writer.write(r"\%s{" % latex_tag)
      writer.write(txt)
      writer.write("}\n")
    DirectlyPrintSub(current_node)(writer, 'latex')
  return PrintTo


def PrintTopLevel(current_node):
  def PrintTo(writer, format='html'):
    if format == 'html':
      PrintInHTMLFormat(writer)
    elif format == 'latex':
      PrintInLatexFormat(writer)
    elif format == 'beamer_latex':
      PrintInBeamerLatexFormat(writer)

  def PrintInBeamerLatexFormat(writer):
    cur_text_lines = current_node.GetText().split("\n")
    title = cur_text_lines[0]
    subtitle = ""
    author = ""
    if len(cur_text_lines) >= 2:
      subtitle = cur_text_lines[1]
    if len(cur_text_lines) >= 3:
      author = cur_text_lines[2]

    writer.write(r"""
    \title{%s}
    \subtitle{%s}
    \author[%s]{%s}
    \date{}

    \begin{frame}
    \maketitle
    \end{frame}
    """ % (title, subtitle, author, author))

    DirectlyPrintSub(current_node)(writer, format='beamer_latex')

  def PrintInLatexFormat(writer):
    writer.write(r"\chapter{")
    writer.write(current_node.GetText())
    writer.write("}\n")
    DirectlyPrintSub(current_node)(writer, format='latex')

  def PrintInHTMLFormat(writer):
    writer.write("<center><h1>")
    writer.write(current_node.GetText())
    writer.write("</h1></center>")
    DirectlyPrintSub(current_node)(writer)
  return PrintTo


def main():
  try:
    argv = gflags.FLAGS(sys.argv)
  except gflags.FlagsError as e:
    print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], gflags.FLAGS)
    sys.exit(1)
  logging.basicConfig(level=logging.INFO)

  if gflags.FLAGS.mindmap_file is None:
    print 'Usage: %s ARGS\n%s' % (sys.argv[0], gflags.FLAGS)
    sys.exit(1)

  org = Organization(
    codecs.open(gflags.FLAGS.mindmap_file, 'r', 'utf8').read())
  if gflags.FLAGS.html_file is not None:
    org.OutputToHTML(gflags.FLAGS.html_file)

  if gflags.FLAGS.beamer_latex_file is not None:
    org.OutputToBeamerLatex(gflags.FLAGS.beamer_latex_file)

  if gflags.FLAGS.latex_file is not None:
    org.OutputToLatex(gflags.FLAGS.latex_file)

if __name__ == "__main__":
  main()
