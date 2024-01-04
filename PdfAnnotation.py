
import ntpath
import json
import pickle
import glob
import functools
import os
import tempfile
import subprocess

#***********************************************************************

def extractPng(pdffile):
    """ Transform each page of the given pdf file to png images and
        return the folder in which the images are stored
    """
    pdfname = os.path.splitext(os.path.basename(pdffile))[0]

    tmpDir = os.path.join(tempfile.gettempdir(), 'tmp_'+pdfname+'_{}'.format(hash(os.times())))
    os.mkdir(tmpDir)
    
    
    subprocess.call(['gs', '-sDEVICE=pngalpha',  '-o',  pdfname+'_%03d.png', '-r288', pdffile], cwd = tmpDir)
    
    return tmpDir

#***********************************************************************
class AnnotedDocument:
    """ The main document on which we want to add annotations """
    
    _pageNumber = 0
    _pageImages = []
    _filePath = ""
    
    #-------------------------------------------------------------------
    def __init__(self, filepath):
        """Constructor"""  
        
        pngDir = extractPng(filepath)
        
        self._pageImages=sorted(glob.glob(pngDir+"/*.png"))
        self._pageNumber = len(self._pageImages)
        self._filePath = filepath
        
    def getPageNb(self):
        return self._pageNumber
        
    def getPageImage(self, pageNb):
        return self._pageImages[pageNb-1]
        
    def getFilePath(self):
        return self._filePath    

#***********************************************************************
class AnnotationObject:
    """ A parent class defining the methods of object that describe
        annotations
    """

    def getText(self):
        return ""
        
    def hasAppendix(self):
        return False
    
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
class TextAnnotation(AnnotationObject):
    text = ""
    
    def __init__(self, t):
        """Constructor""" 
        self.text = t
    
    def getText(self):
        """ Return the text defining this annotation """
        return self.text
        
    def getInfo(self):
        """ Return info about this annotation, i.e. the pages to 
            append, ....
        """
        txt = ""
        return txt

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
class FileAnnotation(AnnotationObject):
    
    filename = ""
    page_to_append = None
    
    def __init__(self, f):
        """Constructor""" 
        self.filename = f
        
        # define page to append
        with open('page_selection.json') as json_file:
            pages = json.load(json_file)
        # retrieve supplier namer
        
        try:
            supplier = f.split("_")[1]
            self.page_to_append = pages[supplier]
        except IndexError:
            # do nothing if there was not token separated by "_"
            pass
        except KeyError:
            # do nothing if the name is not in the dictionary
            pass
        
    
    def getText(self):
        """ Return the text defining this annotation """
        return ntpath.basename(self.filename)
        
    def getInfo(self):
        """ Return info about this annotation, i.e. the pages to 
            append, ....
        """
        txt = ""
        if self.page_to_append:
            txt += "pp"
            for p in self.page_to_append:
                txt+= str(p)
        return txt
        
    def hasAppendix(self):
        return True
                        
    def getPageToAppend(self):
        """ Return which page must be appended when generating the full
            document
            return: * a list containing the number of pages that must be appended
                    * None if all page of document must be appended   
        """    
        return self.page_to_append


#***********************************************************************
class Annotation:
    posX = 0
    posY = 0
    pageNb = 0
    annotationObject = None
    
    def __init__(self, noteObj):
        """Constructor""" 
        self.annotationObject = noteObj   
    
    def setPosition(self, x, y):
        self.posX = x
        self.posY = y
        
    def getText(self):
        return self.annotationObject.getText()

    def getInfo(self):
        return self.annotationObject.getInfo()
        
    def hasAppendix(self):
        return self.annotationObject.hasAppendix()

def compareAnnotation(n1, n2):
    if n1.pageNb == n2.pageNb:
        if n1.posY > n2.posY:
            return 1
        elif n1.posY == n2.posY:
            return 0
        else:
            return -1
    else:
        if n1.pageNb > n2.pageNb:
            return 1
        elif n1.pageNb == n2.pageNb:
            return 0
        else:
            return -1
        

#***********************************************************************
class AnnotationProject:
    
    #-------------------------------------------------------------------
    def __init__(self, filepath):
        """Constructor""" 
    
        self.mainDocument = AnnotedDocument(filepath)

        self.annotations = []

        
        # test annoatations
        #note1 = Annotation(FileAnnotation("Facture01.pdf"));
        #note1.setPosition(0.1, 0.1)
        #note1.pageNb=1
        #self.annotations.append(note1)
        #note2 = Annotation(FileAnnotation("Facture02.pdf"));
        #note2.setPosition(0.1, 0.5) 
        #note2.pageNb=2
        #self.annotations.append(note2)

    def sortAnnotations(self):
        self.annotations.sort(key=functools.cmp_to_key(compareAnnotation))
        
    def printAnnotations(self):
        for n in self.annotations:
            print(n.getText())

#***********************************************************************

def loadProject() :
    fp = open('my_json.pick', 'rb')
    prj = pickle.load(fp)
    fp.close()      
    return prj
    
    
def saveProject(prj):
    fp = open('my_json.pick', 'wb')
    pickle.dump(prj, fp)  
    fp.close()    
    
    
#***********************************************************************
#***********************************************************************
#***********************************************************************

#  EXPORTING THE PROJECT TO PDF

#***********************************************************************


from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.generic import NumberObject, NameObject
# import StringIO
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


import pickle

#annotationProject = loadProject()


#sourceFile = "/home/ndocquier/Documents/test/pyDragAndDrop/gs/Extrait/Extrait.pdf"

def exportAnnotationsToPdf(prj):

    # retrieve the path to the annoted PDF
    sourceFile = prj.mainDocument.getFilePath()
    
    print("sourcfile: "+sourceFile)

    # read the base document PDF
    annotedDocument = PdfFileReader(open(sourceFile, "rb"))
    outputDoc = PdfFileWriter()

    # store the number of pages in the original document
    nbPages = annotedDocument.getNumPages()


    # Annotate the pages of the base document
    annexCount = 0
    dx = -20
    dy = -8
    for i in range (nbPages):
        
        
        packet = io.BytesIO()
        # create a new PDF with Reportlab
        can = canvas.Canvas(packet, pagesize=A4)
        
        # set color
        can.setFillColorRGB(1,0,0)
        
        # insert the annotations for the current page
        for n in prj.annotations:
            if n.pageNb==i+1:
                
                
                text_to_draw = n.getText()
                if n.hasAppendix():
                    annexCount = annexCount+1
                    text_to_draw = "An. "+str(annexCount)+" - "+text_to_draw
                
                can.drawString(n.posX*A4[0]+dx, (1-n.posY)*A4[1]+dy, text_to_draw)
        
        
        can.save()
        
        packet.seek(0)
        
        notePage = PdfFileReader(packet)
        
        page = annotedDocument.getPage(i)
        page.mergePage(notePage.getPage(0))
        
        outputDoc.addPage(page)
        
    # Append the apendix documents
    annexCount = 0

    for n in prj.annotations:
        
        if not n.hasAppendix():
            continue
        
        # increment the appendix counter
        annexCount = annexCount+1
        
        # get the PDF of the appendix document
        apendixDoc = PdfFileReader(open(n.annotationObject.filename, "rb"))

        # annotate each page of the appendix doc and append it to the global output doc
        for i in range(apendixDoc.getNumPages()):
            
            page_to_append = n.annotationObject.page_to_append
            if (not page_to_append) or (page_to_append and i+1 in page_to_append):
                
                print("Adding annotation on page "+str(i))
                
                # Retrieve the appendix current page
                page = apendixDoc.getPage(i)
                
                
                # Retrieve rotation angle of the current page
                appendixRotate = page.get('/Rotate', 0)
                appendixAngle = appendixRotate if isinstance(appendixRotate, int) else appendixRotate.getObject()
                            
                # Retrieve page dimensions
                appendixSize = apendixDoc.getPage(0).mediaBox[2:4]
                pageWidth = appendixSize[0]
                pageHeight = appendixSize[1]
                
            
                # If page is rotated, invert page dimensions
                if appendixAngle%180:
                    pageWidth = appendixSize[1]
                    pageHeight = appendixSize[0]
                    appendixSize[0] = pageWidth
                    appendixSize[1] = pageHeight         
                
                # - - - - - - - - - - - - - - - - - - - - - - - -
                # Create a canvas to add annotation (file name of the appendix doc)
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=appendixSize)
                
                # set color
                can.setFillColorRGB(1,0,0)
                
                # insert the file name of the document
                print("Adding appendix ("+str(150)+", "+str(0.985*pageHeight.as_numeric())+")--->" + "Annexe " + str(annexCount) +" - "+n.getText() )

                can.drawString(150, 0.985*pageHeight.as_numeric(), "Annexe " + str(annexCount) +" - "+n.getText())

                #can.rect(150, 0.9*A4[1], 150, 50, fill=1)
                #can.linkURL('http://google.com', (150, 0.9*A4[1], 150, 50), relative=1)

                can.save()
                
                packet.seek(0)
                annotationDoc = PdfFileReader(packet)            
                
                annotationPage = annotationDoc.getPage(0)

                # - - - - - - - - - - - - - - - - - - - - - - - -
                
                
                
                if appendixAngle:
                    print("Rotate page, angle: "+str(appendixAngle)+" - w:"+str(pageWidth)+" - h "+str(pageHeight))
                    # page.mergeRotatedPage(notePageObj, appendixAngle, True)
                    # page.mergeRotatedTranslatedPage(notePageObj, appendixAngle, notePageObj.mediaBox.getWidth() / 2, notePageObj.mediaBox.getHeight() / 2)
                    
                    # page.mergeRotatedTranslatedPage(annotationPage, appendixAngle, pageWidth/2,pageWidth/2, True)
                    x_rotate = min(pageWidth, pageHeight)/2
                    page.mergeRotatedTranslatedPage(annotationPage, appendixAngle, x_rotate, x_rotate, True)
                else:
                    page.mergePage(annotationPage)
                
                outputDoc.addPage(page) 
        
    # finally, write "output" to a real file
    outputStream = open("testout.pdf", "wb")
    outputDoc.write(outputStream)
    outputStream.close()
    
    
#***********************************************************************
#***********************************************************************
#***********************************************************************

import wx


 
########################################################################
class MainPanel(wx.Panel):
    """"""

    ImWidth=300
    ImHeight=350
    
    noteToDraw = []
 
    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        #self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.frame = parent
 
        
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.bmp = None
 
    #----------------------------------------------------------------------
    def OnEraseBackground(self, evt):
        """
        Add a picture to the background
        """
        # yanked from ColourDB.py
        dc = evt.GetDC()
 
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        #bmp = wx.Bitmap("./AGC.jpg")
        
        #bmp.SetWidth(300)

        self.ImWidth=self.ImWidth+1

        panSize = self.GetSize()
        
        # Draw the current page as the background image
        if self.bmp is not None:
            #image = wx.ImageFromBitmap(bmp)
            image = self.bmp.ConvertToImage()
            #image = image.Scale(self.ImWidth, self.ImHeight, wx.IMAGE_QUALITY_HIGH)
            newWidth = float(panSize.GetWidth())/self.bmp.GetWidth()
            newHeight = float(panSize.GetHeight())/self.bmp.GetHeight()
            #print "size: w="+str(newWidth)+" - h="+str(newHeight)
            image = image.Scale(panSize.GetWidth(),
                                panSize.GetHeight(),
                                wx.IMAGE_QUALITY_HIGH)
            resizedBmp = wx.Bitmap(image)        
            
            dc.DrawBitmap(resizedBmp, 0, 0)
        
        
        # draw the annotations
        notes = self.noteToDraw
        dc.SetTextBackground(wx.RED)
        dc.SetTextForeground(wx.RED)
        i=0
        for n in notes:
            
            text_to_draw = n.getText() + "  ["+n.getInfo()+"]"
            if n.hasAppendix():
                i=i+1
                text_to_draw = "An. "+str(i)+": "+text_to_draw
            dc.DrawText(text_to_draw, n.posX*panSize.GetWidth(), n.posY*panSize.GetHeight())
            

    #----------------------------------------------------------------------
    def setImageFile(self, imagefile):
        self.bmp = wx.Bitmap(imagefile)



########################################################################
class FileAnnotationDropTarget(wx.FileDropTarget):
    """ Manage the drag and drop of new files on the main document
    
    """
 
    #----------------------------------------------------------------------
    def __init__(self, panel):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.panel = panel
 
    #----------------------------------------------------------------------
    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        #self.window.SetInsertionPointEnd()
        #self.window.updateText("\n%d file(s) dropped at %d,%d:\n" % (len(filenames), x, y))
        print("\n%d file(s) dropped at %d,%d:\n" % (len(filenames), x, y))
        
        newNote = Annotation(FileAnnotation(filenames[0]))
        newNote.setPosition(float(x)/self.panel.GetSize().GetWidth(),
                            float(y)/self.panel.GetSize().GetHeight())
        self.panel.frame.addAnnotation(newNote)

########################################################################
class FileTextAnnotationDropTarget(wx.TextDropTarget):
 
    #----------------------------------------------------------------------
    def __init__(self, panel):
        wx.TextDropTarget.__init__(self)
        self.panel = panel
 
    #----------------------------------------------------------------------
    def OnDropText(self, x, y, text):
        
        # Check whether text corresponds to a file
        is_file = False
        if text.startswith("file:///"):
            filename = text[7:].strip()
            if os.path.isfile(filename):
                is_file = True
                print("\nA file dropped at %d,%d:\n" % (x, y))
                
                newNote = Annotation(FileAnnotation(filename))
                newNote.setPosition(float(x)/self.panel.GetSize().GetWidth(),
                                    float(y)/self.panel.GetSize().GetHeight())
                self.panel.frame.addAnnotation(newNote)
        if not is_file:
            newNote = Annotation(TextAnnotation(text))
            newNote.setPosition(float(x)/self.panel.GetSize().GetWidth(),
                                float(y)/self.panel.GetSize().GetHeight())
            self.panel.frame.addAnnotation(newNote)            
        
 
    #----------------------------------------------------------------------
    def OnDragOver(self, x, y, d):
        return wx.DragCopy


########################################################################
class MainFrame(wx.Frame):
    """"""
 
    pageId = 0
    
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        #self.load()
        self.annotationProject = None
        # self.annotationProject = AnnotationProject(os.path.join(os.getcwd(),"Extrait/ReleveMastercard_20230707.pdf"))
        # self.annotationProject = AnnotationProject(os.path.join(os.getcwd(),"Extrait/Extrait_2023T3.pdf"))


        wx.Frame.__init__(self, None, size=(600,450))
        self.panel = MainPanel(self)        
        self.Center()
        
        
        # file_drop_target = FileAnnotationDropTarget(self.panel)
        file_drop_target = FileTextAnnotationDropTarget(self.panel)
        self.panel.SetDropTarget(file_drop_target) 
        
        # - - - - 
        # Toolbar
        # - - - - 
        tb = wx.ToolBar( self, -1 ) 
        self.ToolBar = tb 
        # buttons to manage current page 
        newBut = tb.AddTool(wx.ID_ANY, "new", wx.Bitmap("icon/icone_new.png") ) 
        prevBut = tb.AddTool(wx.ID_ANY, "prev", wx.Bitmap("icon/icone_stepBackward.png") ) 
        nextBut = tb.AddTool(wx.ID_ANY, "next", wx.Bitmap("icon/icone_stepForward.png")) 
        saveBut = tb.AddTool(wx.ID_ANY, "save", wx.Bitmap("icon/icone_save.png")) 
        loadBut = tb.AddTool(wx.ID_ANY, "load", wx.Bitmap("icon/icone_open.png")) 
        exportBut = tb.AddTool(wx.ID_ANY, "export", wx.Bitmap("icon/icone_generate.png")) 
        tb.Bind(wx.EVT_TOOL, self.newProject, source=newBut)
        tb.Bind(wx.EVT_TOOL, self.prevPage, source=prevBut)
        tb.Bind(wx.EVT_TOOL, self.nextPage, source=nextBut)
        tb.Bind(wx.EVT_TOOL, self.save, source=saveBut)
        tb.Bind(wx.EVT_TOOL, self.load, source=loadBut)
        tb.Bind(wx.EVT_TOOL, self.export, source=exportBut)
        
        tb.Realize() 
        # - - - - 
        
        self.pageId=1
        self.updatePage()
        
        
        print("RELOAD")
        #self.load() 
        

    def setImageFile(self, imagefile):
        self.panel.setImageFile(imagefile)
    
    def openPdfFile(self, pdfFilename):
        self.annotationProject = AnnotationProject(pdfFilename)
        self.pageId = 1
        self.updatePage()        
    
    def newProject(self, e):
        """ Open a dialog to choose a PDF file to annotate and
            then create a new AnnotationProject if a correct file is
            selected.
        """
        print("New project")
        with wx.FileDialog(self, "Open PDF file to annotate", wildcard="PDF files (*.pdf)|*.pdf",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # Proceed loading the file chosen by the user
            pdfFilename = fileDialog.GetPath()
            try:
                self.openPdfFile(pdfFilename)
            except IOError:
                print("Error while opening PDF file '%s'." % pdfFilename)
                wx.LogError("Cannot open file '%s'." % pdfFilename)         
        

    def nextPage(self, e):
        print("Next page")
        self.pageId = self.pageId+1
        self.updatePage()

    def prevPage(self, e):
        print("Prev page")
        self.pageId = self.pageId-1
        self.updatePage()
        
    def updatePage(self):
        if self.annotationProject is None:
            return
            
        doc = self.annotationProject.mainDocument
        if self.pageId<1:
            self.pageId = doc.getPageNb()
        elif self.pageId>doc.getPageNb():
            self.pageId = 1
            
        # update the list of note to be drawn
        print("pageId: "+str(self.pageId))
        print(self.annotationProject.mainDocument._pageImages)
        self.setImageFile(self.annotationProject.mainDocument.getPageImage(self.pageId))    
        self.setNoteToDraw()
        self.panel.Refresh()
        
    def addAnnotation(self, note):
        note.pageNb = self.pageId
        self.annotationProject.annotations.append(note)
        
        self.annotationProject.sortAnnotations()
        
        self.setNoteToDraw()
        self.panel.Refresh()
        
        print("Add note....")
        
    def setNoteToDraw(self):
        for n in self.annotationProject.annotations:
            print("page number:"+str(n.pageNb))
        newNotes = [n for n in self.annotationProject.annotations if n.pageNb==self.pageId]
        print("Current page"+str(self.pageId))
        print(newNotes)
        self.panel.noteToDraw = newNotes
        
    def save(self, e):
        fp = open('my_json.pick', 'wb')
        pickle.dump(self.annotationProject, fp)  
        fp.close()
            
    def load(self, e=None):
        fp = open('my_json.pick', 'rb')
        self.annotationProject = pickle.load(fp)
        print(self.annotationProject.mainDocument._pageImages)
        fp.close()  
        self.updatePage()    
        
    def export(self, e=None):
        exportAnnotationsToPdf(self.annotationProject)
        

########################################################################



########################################################################


class Main(wx.App):
    """"""
    
 
    #----------------------------------------------------------------------
    def __init__(self, redirect=False, filename=None):
        """Constructor"""
        wx.App.__init__(self, redirect, filename)
        dlg = MainFrame()
        dlg.Show()
 
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = Main()
    
    app.MainLoop()
