
import ntpath
import json
import pickle
import glob

#***********************************************************************
class AnnotedDocument:
    """ The main document on which we want to add annotations """
    
    _pageNumber = 0
    _pageImages = []
    
    #-------------------------------------------------------------------
    def __init__(self, filepath):
        """Constructor"""  
        
        self._pageImages=sorted(glob.glob(filepath+"/*.png"))
        self._pageNumber = len(self._pageImages)
        print self._pageImages
        
    def getPageNb(self):
        return self._pageNumber
        
    def getPageImage(self, pageNb):
        return self._pageImages[pageNb-1]

#***********************************************************************
class AnnotationObject:
    """ A parent class defining the methods of object that describe
        annotations
    """

    def getText(self):
        return ""
    
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
class TextAnnotation(AnnotationObject):
    text = "hello"
    
    def getText(self):
        return text

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
class FileAnnotation(AnnotationObject):
    
    filename = ""
    
    def __init__(self, f):
        """Constructor""" 
        self.filename = f
    
    def getText(self):
        return ntpath.basename(self.filename)
    

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
        self.bmp = wx.Bitmap("./test.png")
 
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
        
        

        #image = wx.ImageFromBitmap(bmp)
        image = self.bmp.ConvertToImage()
        #image = image.Scale(self.ImWidth, self.ImHeight, wx.IMAGE_QUALITY_HIGH)
        newWidth = float(panSize.GetWidth())/self.bmp.GetWidth()
        newHeight = float(panSize.GetHeight())/self.bmp.GetHeight()
        #print "size: w="+str(newWidth)+" - h="+str(newHeight)
        image = image.Scale(panSize.GetWidth(),
                            panSize.GetHeight(),
                            wx.IMAGE_QUALITY_HIGH)
        resizedBmp = wx.BitmapFromImage(image)        
        
        dc.DrawBitmap(resizedBmp, 0, 0)
        
        
        # draw the annotations
        notes = self.noteToDraw
        dc.SetTextBackground(wx.RED)
        dc.SetTextForeground(wx.RED)
        for n in notes:
            dc.DrawText(n.getText(), n.posX*panSize.GetWidth(), n.posY*panSize.GetHeight())
            

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
class MainFrame(wx.Frame):
    """"""
 
    pageId = 0
    annotationProject = None
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        #self.load()
        self.annotationProject = AnnotationProject("/home/ndocquier/Documents/test/pyDragAndDrop/gs/Extrait")


        wx.Frame.__init__(self, None, size=(600,450))
        self.panel = MainPanel(self)        
        self.Center()
        
        
        file_drop_target = FileAnnotationDropTarget(self.panel)
        self.panel.SetDropTarget(file_drop_target) 
        
        # - - - - 
        # Toolbar
        # - - - - 
        tb = wx.ToolBar( self, -1 ) 
        self.ToolBar = tb 
        #buttons to manage current page 
        prevBut = tb.AddTool(101, wx.Bitmap("icon/icone_stepBackward.png") ) 
        nextBut = tb.AddTool(102,wx.Bitmap("icon/icone_stepForward.png")) 
        saveBut = tb.AddTool(103,wx.Bitmap("icon/icone_save.png")) 
        loadBut = tb.AddTool(104,wx.Bitmap("icon/icone_open.png")) 
        tb.Bind(wx.EVT_TOOL, self.prevPage, source=prevBut)
        tb.Bind(wx.EVT_TOOL, self.nextPage, source=nextBut)
        tb.Bind(wx.EVT_TOOL, self.save, source=saveBut)
        tb.Bind(wx.EVT_TOOL, self.load, source=loadBut)
        
        tb.Realize() 
        # - - - - 
        
        self.pageId=1
        self.updatePage()
        
        
        print "RELOAD"
        #self.load() 
        

    def setImageFile(self, imagefile):
        self.panel.setImageFile(imagefile)
    
    
    def nextPage(self, e):
        print "Next page"
        self.pageId = self.pageId+1
        self.updatePage()

    def prevPage(self, e):
        print "Prev page"
        self.pageId = self.pageId-1
        self.updatePage()
        
    def updatePage(self):
        doc = self.annotationProject.mainDocument
        if self.pageId<1:
            self.pageId = doc.getPageNb()
        elif self.pageId>doc.getPageNb():
            self.pageId = 1
            
        # update the list of note to be drawn
        print "pageId: "+str(self.pageId)
        print self.annotationProject.mainDocument._pageImages
        self.setImageFile(self.annotationProject.mainDocument.getPageImage(self.pageId))    
        self.setNoteToDraw()
        self.panel.Refresh()
        
    def addAnnotation(self, note):
        note.pageNb = self.pageId
        self.annotationProject.annotations.append(note)
        self.setNoteToDraw()
        self.panel.Refresh()
        
    def setNoteToDraw(self):
        for n in self.annotationProject.annotations:
            print "page number:"+str(n.pageNb)
        newNotes = [n for n in self.annotationProject.annotations if n.pageNb==self.pageId]
        print "Current page"+str(self.pageId)
        print newNotes
        self.panel.noteToDraw = newNotes
        
    def save(self, e):
        fp = open('my_json.pick', 'wb')
        pickle.dump(self.annotationProject, fp)  
        fp.close()
            
    def load(self, e=None):
        fp = open('my_json.pick', 'rb')
        self.annotationProject = pickle.load(fp)
        print self.annotationProject.mainDocument._pageImages
        fp.close()  
        self.updatePage()    
        
        
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
