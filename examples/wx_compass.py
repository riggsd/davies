#!/usr/bin/env python
# See: https://github.com/wxWidgets/wxPython/blob/master/demo/DVC_DataViewModel.py

import sys

import wx
import wx.grid as grid
import wx.dataview as dv

from davies import compass


class ProjectTreeListModel(dv.PyDataViewModel):
    """This model maps our Compass Project structure to wx DataView"""

    def __init__(self, project):
        dv.PyDataViewModel.__init__(self)
        self.project = project

        self.objmapper.UseWeakRefs(True)

    def GetColumnCount(self):
        return 3

    def GetColumnType(self, col):
        columns = {0: 'string', 1: 'string', 2: 'string'}
        return columns[col]

    def GetChildren(self, parent, children):
        if not parent:
            children.append(self.ObjectToItem(self.project))
            return 1

        node = self.ItemToObject(parent)

        if isinstance(node, compass.Project):
            for dat in node.linked_files:
                children.append(self.ObjectToItem(dat))
            return len(node)

        if isinstance(node, compass.DatFile):
            for survey in node.surveys:
                children.append(self.ObjectToItem(survey))
            return len(node)

        return 0

    def IsContainer(self, item):
        if not item:
            return True

        node = self.ItemToObject(item)

        if isinstance(node, compass.Project):
            return True

        if isinstance(node, compass.DatFile):
            return True

        return False

    def HasContainerColumns(self, item):
        node = self.ItemToObject(item)

        if isinstance(node, compass.Survey):
            return True

        return False

    def GetParent(self, item):
        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject()

        if isinstance(node, compass.Project):
            return dv.NullDataViewItem

        if isinstance(node, compass.DatFile):
            return self.project

        if isinstance(node, compass.Survey):
            for dat in self.project:
                if node in dat:
                    return dat

        raise RuntimeError('Unable to find parent of %s (%s)' % (node, node.__class__.__name__))

    def GetValue(self, item, col):
        node = self.ItemToObject(item)

        if isinstance(node, compass.Project):
            vals = {0: node.name, 1: '', 2: ''}
            return vals[col]

        if isinstance(node, compass.DatFile):
            vals = {0: node.name, 1: '', 2: ''}
            return vals[col]

        if isinstance(node, compass.Survey):
            vals = {0: node.name, 1: str(node.date), 2: node.comment}
            return vals[col]

        raise RuntimeError('Unknown node type: %s (%s)' % (node, node.__class__.__name__))


#----------------------------------------------------------------------

class TestPanel(wx.Panel):
    def __init__(self, parent, data=None, model=None):
        wx.Panel.__init__(self, parent, -1)

        # Create a dataview control
        self.dvc = dv.DataViewCtrl(self,
                                   style=wx.BORDER_THEME
                                   | dv.DV_ROW_LINES # nice alternating bg colors
                                   #| dv.DV_HORIZ_RULES
                                   | dv.DV_VERT_RULES
                                   | dv.DV_MULTIPLE
                                   )

        # Create an instance of our model...
        if model is None:
            self.model = ProjectTreeListModel(data)
        else:
            self.model = model

        # Tel the DVC to use the model
        self.dvc.AssociateModel(self.model)

        # Define the columns that we want in the view.  Notice the
        # parameter which tells the view which col in the data model to pull
        # values from for each view column.
        # if 1:
        #     self.tr = tr = dv.DataViewTextRenderer()
        #     c0 = dv.DataViewColumn("Name",   # title
        #                            tr,        # renderer
        #                            0,         # data model column
        #                            width=80)
        #     self.dvc.AppendColumn(c0)
        # else:
        c0 = self.dvc.AppendTextColumn("Name",   0, width=160)
        c0.Alignment = wx.ALIGN_LEFT
        c0.Sortable = True

        c1 = self.dvc.AppendTextColumn("Date",   1, width=90) #, mode=dv.DATAVIEW_CELL_EDITABLE)
        c1.Alignment = wx.ALIGN_CENTER
        c1.Sortable = True

        c2 = self.dvc.AppendTextColumn("Comment",    2, width=300) #, mode=dv.DATAVIEW_CELL_EDITABLE)
        c2.Alignment = wx.ALIGN_LEFT

        # Set some additional attributes for all the columns
        # for c in self.dvc.Columns:
        #     c.Sortable = True
        #     c.Reorderable = True

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.dvc, 1, wx.EXPAND)


class MyFrame(wx.Frame):
    """Our customized window class"""

    def __init__(self, parent, id, title, project=None):
        """Initialize our window"""
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(450, 350))

        self.CreateStatusBar()

        # Create File menu
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu_new  = file_menu.Append(wx.ID_NEW,  '&New',  'New project file')
        file_menu_open = file_menu.Append(wx.ID_OPEN, '&Open', 'Open project file')
        file_menu_save = file_menu.Append(wx.ID_SAVE, '&Save', 'Save project file')
        file_menu_quit = file_menu.Append(wx.ID_EXIT, '&Quit', 'Quit application')
        menubar.Append(file_menu, '&File')
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnOpen, file_menu_open)
        self.Bind(wx.EVT_MENU, self.OnQuit, file_menu_quit)

        # Create a splitter window
        self.splitter = wx.SplitterWindow(self, -1)

        # Create the left panel
        self.leftPanel = leftPanel = TestPanel(self.splitter, project)
        self.dvc = leftPanel.dvc

        # Create a box sizer that will contain the left panel contents
        leftBox = wx.BoxSizer(wx.VERTICAL)

        # Add the DVC to the box sizer
        #leftBox.Add(self.dvc, 1, wx.EXPAND)

        # Bind the OnSelChanged method to the DVC
        self.dvc.Bind(dv.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelChanged)

        # Set the size of the right panel to that required by the tree
        leftPanel.SetSizer(leftBox)

        # Create the right panel
        rightPanel = wx.Panel(self.splitter, -1)
        # Create the right box sizer that will contain the panel's contents
        rightBox = wx.BoxSizer(wx.VERTICAL)
        # Create a widget to display static text and store it in the right
        # panel
        self.display = wx.StaticText(rightPanel, -1, '', (10, 10), style=wx.ALIGN_LEFT)
        # Add the display widget to the right panel
        rightBox.Add(self.display, -1, wx.EXPAND)
        # Set the size of the right panel to that required by the
        # display widget
        rightPanel.SetSizer(rightBox)
        # Put the left and right panes into the split window
        self.splitter.SplitVertically(leftPanel, rightPanel)
        # Create the window in the centre of the screen
        self.Centre()

    def OnSelChanged(self, event):
        """Method called when selected item is changed"""
        # Get the selected item object
        item = event.GetItem()
        obj = self.leftPanel.model.ItemToObject(item)
        if isinstance(obj, compass.Survey):
            l = [
                'Survey Name: %s' % obj.name,
                'Survey Date: %s' % obj.date,
                'Comment: %s' % obj.comment,
                'Team: %s' % ', '.join(obj.team),
                'Surveyed Footage: %0.1f' % obj.length,
                '',
                ]
            l.extend(['  '.join(['%s: %s' % (k,v) for (k,v) in shot.items()]) for shot in obj.shots])
            self.display.SetLabel(str('\n'.join(l)))
        else:
            self.display.SetLabel('')

    def OnQuit(self, event):
        self.Close()

    def OnOpen(self, event):
        open_dialog = wx.FileDialog(self, 'Open Compass Project .MAK', '', '', 'Project files (*.mak)|*.mak', wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if open_dialog.ShowModal() == wx.ID_CANCEL:
            return
        self.load_project(open_dialog.GetPath())

    def load_project(self, makfilename):

        self.tree.DeleteAllItems()
        root = self.tree.AddRoot(project.name)
        for linked_file in project.linked_files:
            dat = self.tree.AppendItem(root, linked_file.name)
            for survey in linked_file.surveys:
                self.tree.AppendItem(dat, survey.name)
        self.tree.Expand(root)


class MyApp(wx.App):
    """Our application class"""

    def OnInit(self):
        """Initialize by creating the split window with the tree"""
        project = compass.CompassProjectParser(sys.argv[1]).parse()
        frame = MyFrame(None, -1, 'wxCompass', project)
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()
