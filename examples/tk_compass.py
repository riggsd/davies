#!/usr/bin/env python
"""
Tkinter GUI for editing Compass projects.
"""

from Tkinter import *
import ttk
import tkFileDialog

import sys
import logging

from davies import compass
from davies.event import event


class OffsetShotEditor(ttk.Frame):
    """Offset survey paper style editor for Survey shots."""

    NUM_SHOTS = 20

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)

        self.stations = []
        self.distances = []
        self.azm_fss, self.azm_bss = [], []
        self.clino_fss, self.clino_bss = [], []
        self.lefts, self.rights, self.ups, self.downs = [], [], [], []
        self.comments = []
        #for i in range(22):
        #    self.rowconfigure(i, weight=1)
        #for i in range(11):
        #    self.columnconfigure(i, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(10, weight=10)

        ttk.Label(self, text='STA').grid(row=0, column=0, rowspan=2, sticky=S)
        ttk.Label(self, text=' ').grid(row=0, column=1, columnspan=5)
        ttk.Label(self, text='DIST').grid(row=1, column=1, rowspan=2, sticky=S)
        ttk.Label(self, text='AZM').grid(row=1, column=2, rowspan=2, sticky=S)
        ttk.Label(self, text='INC').grid(row=1, column=4, rowspan=2, sticky=S)
        ttk.Label(self, text='L').grid(row=0, column=6, rowspan=2, sticky=S)
        ttk.Label(self, text='R').grid(row=0, column=7, rowspan=2, sticky=S)
        ttk.Label(self, text='U').grid(row=0, column=8, rowspan=2, sticky=S)
        ttk.Label(self, text='D').grid(row=0, column=9, rowspan=2, sticky=S)
        ttk.Label(self, text='NOTE').grid(row=0, column=10, rowspan=2, sticky=S)

        ro = 2  # frame row offset
        for i in range(2 * OffsetShotEditor.NUM_SHOTS + 1):
            if i % 2 == 0:
                # station-oriented

                station = StringVar()
                self.stations.append(station)
                ttk.Entry(self, width=6, textvariable=station).grid(row=i+ro, column=0, rowspan=2)

                l = IntVar()
                self.lefts.append(l)
                ttk.Entry(self, width=3, textvariable=l, justify=RIGHT).grid(row=i+ro, column=6, rowspan=2)

                r = IntVar()
                self.rights.append(r)
                ttk.Entry(self, width=3, textvariable=r, justify=RIGHT).grid(row=i+ro, column=7, rowspan=2)

                u = IntVar()
                self.ups.append(u)
                ttk.Entry(self, width=3, textvariable=u, justify=RIGHT).grid(row=i+ro, column=8, rowspan=2)

                d = IntVar()
                self.downs.append(d)
                ttk.Entry(self, width=3, textvariable=d, justify=RIGHT).grid(row=i+ro, column=9, rowspan=2)

                comment = StringVar()
                self.comments.append(comment)
                ttk.Entry(self, width=10, textvariable=comment).grid(row=i+ro, column=10, rowspan=2, sticky=E+W)

            else:
                # shot-oriented

                dist = StringVar() # DoubleVar()
                self.distances.append(dist)
                ttk.Entry(self, width=6, textvariable=dist, justify=RIGHT).grid(row=i+ro, column=1, rowspan=2)

                azm_fs = StringVar() # DoubleVar()
                self.azm_fss.append(azm_fs)
                ttk.Entry(self, width=6, textvariable=azm_fs, justify=RIGHT).grid(row=i+ro, column=2, rowspan=2)

                clino_fs = StringVar() # DoubleVar()
                self.clino_fss.append(clino_fs)
                ttk.Entry(self, width=5, textvariable=clino_fs, justify=RIGHT).grid(row=i+ro, column=4, rowspan=2)

    def populate(self, shots):
        # TODO: some surveys may have LRUD associated with the 'TO' station rather than 'FROM' station
        vars = self.stations, self.distances, self.azm_fss, self.clino_fss, self.lefts, self.rights, self.ups, self.downs, self.comments
        keys = 'FROM', 'LENGTH', 'BEARING', 'INC', 'LEFT', 'RIGHT', 'UP', 'DOWN', 'COMMENTS'
        offset_keys = 'LENGTH', 'BEARING', 'INC'
        prev_station = None
        ro = 0  # row offset
        for i, shot in enumerate(shots[:2*OffsetShotEditor.NUM_SHOTS+1/2]):
            print shot
            if prev_station and shot['FROM'] != prev_station:
                ro += 1
            for var, key in zip(vars, keys):
                row = i+ro if key in offset_keys else i
                var[row].set(shot.get(key, ''))
            prev_station = shot['TO']
        self.stations[len(shots) + ro].set(prev_station)


class SurveyEditor(ttk.Frame):
    """Compass Survey editor Frame."""

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)  # 2x1
        self.grid(row=0, column=0, sticky=N+S+E+W)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.header_frame = header_frame = ttk.Frame(self)  # 4x3
        header_frame.grid(row=0, column=0, sticky=E+W)
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=10)
        header_frame.columnconfigure(2, weight=1)
        header_frame.columnconfigure(3, weight=10)

        self.name = StringVar()
        self.date = StringVar()
        self.comment = StringVar()
        self.team = StringVar()

        ttk.Label(header_frame, text='Name:', anchor=E).grid(row=0, column=0)
        ttk.Entry(header_frame, textvariable=self.name, width=9).grid(row=0, column=1, sticky=E+W)

        ttk.Label(header_frame, text='Date:', anchor=E).grid(row=0, column=2)
        ttk.Entry(header_frame, textvariable=self.date, width=9).grid(row=0, column=3, sticky=E+W)

        ttk.Label(header_frame, text='Comment:', anchor=E).grid(row=1, column=0)
        ttk.Entry(header_frame, textvariable=self.comment, width=40).grid(row=1, column=1, columnspan=3, sticky=E+W)

        ttk.Label(header_frame, text='Team:', anchor=E).grid(row=2, column=0)
        ttk.Entry(header_frame, textvariable=self.team, width=40).grid(row=2, column=1, columnspan=3, sticky=E+W)

        self.shot_frame = shot_frame = OffsetShotEditor(self)
        shot_frame.grid(row=1, column=0, sticky=N+S+E+W)

    def populate(self, survey):
        self.name.set(survey.name)
        self.date.set(survey.date)
        self.comment.set(survey.comment)
        self.team.set(', '.join(survey.team))

        self.shot_frame.populate(survey.shots)


class ProjectTreeview(ttk.Treeview):
    """Treeview widget for rendering and navigating Compass Project/DatFile/Survey hierarchy."""

    COLUMNS = ('date', 'footage', 'comment')

    def __init__(self, parent, **kwargs):
        ttk.Treeview.__init__(self, parent, selectmode='browse', columns=ProjectTreeview.COLUMNS, **kwargs)
        self.heading('#0', text='Name')
        self.heading('date', text='Date')
        self.column('date', stretch=FALSE, width=100)
        self.heading('footage', text='Length')
        self.column('footage', stretch=FALSE, width=100, anchor=E)
        self.heading('comment', text='Comment')
        self.tag_configure('project', font='* 14 bold')
        self.tag_configure('datfile', font='* 12 bold')
        self.bind('<<TreeviewSelect>>', self.onTreeSelect)
        #self.tag_bind('survey', '<1>', self.onSelectSurvey)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky=N+S+E+W)

        self.current_project_iid = self.current_datfile_iid = self.current_survey_iid = ''

    def reset(self):
        for child_iid in self.get_children():
            self.delete(child_iid)
        self.current_project_iid = self.current_datfile_iid = self.current_survey_iid = ''

    def doSetProject(self, project):
        self.reset()
        self.current_project_iid = self.insert('', 'end', '', text=project.name, values=('', '', ''), open=TRUE, tags=('project',))

    def doAddDatfile(self, datfile):
        values = '', '%0.1f' % datfile.length, ''
        self.current_datfile_iid = self.insert(self.current_project_iid, 'end', text=datfile.name, values=values, tags=('datfile',))

    def doAddSurvey(self, survey):
        values = str(survey.date), '%0.1f' % survey.length, survey.comment
        self.current_survey_iid = self.insert(self.current_datfile_iid, 'end', text=survey.name, values=values, tags=('survey',))

    @event
    def survey_selected(self, datfilename, surveyname):
        """Event fired when a Survey node has been selected"""

    @event
    def datfile_selected(self, datfilename):
        """Event fired when a DatFile node has been selected"""

    @event
    def project_selected(self):
        """Event fired when the Project top-level node has been selected"""

    def onTreeSelect(self, e):
        node_iid = self.focus()
        node = self.item(node_iid)
        if 'survey' in node['tags']:
            surveyname = node['text']
            datfilename = self.item(self.parent(node_iid))['text']
            self.survey_selected(datfilename, surveyname)
        # TODO: datfile, project


class AppGui(ttk.Frame):
    """Main application GUI."""

    def __init__(self, parent, **kwargs):
        ttk.Frame.__init__(self, parent, **kwargs)
        self.parent = parent

        menubar = Menu(parent)
        parent['menu'] = menubar
        menu_file = Menu(menubar)
        menu_file.add_command(label='Open', command=self.openFile)
        menubar.add_cascade(menu=menu_file, label='File')

        mainframe = ttk.Frame(parent, padding=5)  # encapsulates entire main application, 1x2
        mainframe.grid(row=0, column=0, sticky=N+S+E+W)
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        pane = ttk.Panedwindow(mainframe, orient=HORIZONTAL)  # encapsulates project tree and edit form
        pane.grid(row=0, column=0, sticky=N+S+E+W)
        #pane.grid_propagate(False)

        treeframe = ttk.Frame(pane, relief='sunken', padding=5)  # encapsulates project tree, 1x1
        pane.add(treeframe, weight=1)
        #treeframe.grid(row=0, column=0, sticky=N+S+E+W)
        treeframe.columnconfigure(0, weight=1)
        treeframe.rowconfigure(0, weight=1)

        self.tree = tree = ProjectTreeview(treeframe)
        self.tree.survey_selected += self.OnSurveySelected

        self.editframe = editframe = ttk.Frame(pane, relief='sunken', padding=5)  # encapsulates edit form, 1x1
        pane.add(editframe, weight=1)
        #editframe.grid(row=0, column=1, sticky=N+S+E+W)
        editframe.columnconfigure(0, weight=1)
        editframe.rowconfigure(0, weight=1)
        self.editor = None

    def openFile(self):
        filetypes = [('Compass Project Files', ('*.MAK', '*.mak'))]
        makfilename = tkFileDialog.askopenfilename(title='Choose a Compass Project file', defaultextension='.MAK', filetypes=filetypes)
        if makfilename:
            self.OnProjectOpen(makfilename)

    @event
    def OnProjectOpen(self, makfilename):
        """Event fired when user has selected a new Project file to open"""

    @event
    def OnSurveySelected(self, datfilename, surveyname):
        """Event fired when user clicks a Survey node"""

    def doSetProject(self, project):
        self.parent.title(project.name)
        self.tree.doSetProject(project)

    def doAddDatfile(self, datfile):
        self.tree.doAddDatfile(datfile)

    def doAddSurvey(self, survey):
        self.tree.doAddSurvey(survey)

    def doSurveySelected(self, survey):
        if self.editor:
            self.editor.grid_remove()
        self.editor = editor = SurveyEditor(self.editframe)
        editor.grid(row=0, column=0, sticky=N+S+E+W)
        editor.populate(survey)


class AppController(object):

    def __init__(self, parent):
        self.project = None
        self.ui = AppGui(parent, height=600, width=800)
        self.wire_model()
        self.wire_ui()

    def wire_model(self):
        pass

    def wire_ui(self):
        self.ui.OnProjectOpen += self.doOpenProject
        self.ui.OnSurveySelected += self.doSurveySelected

    def doOpenProject(self, makfilepath):
        self.project = compass.CompassProjectParser(makfilepath).parse()
        self.ui.doSetProject(self.project)
        for datfile in self.project:
            self.ui.doAddDatfile(datfile)
            for survey in datfile:
                self.ui.doAddSurvey(survey)

    def doSurveySelected(self, datfilename, surveyname):
        survey = self.project[datfilename][surveyname]
        self.ui.doSurveySelected(survey)


def main(parent):
    app = AppController(parent)


if __name__ == '__main__':
    log_level = logging.DEBUG if '--verbose' in sys.argv else logging.INFO
    logging.basicConfig(level=log_level)

    root = Tk()
    root.option_add('*tearOff', FALSE)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    main(root)

    root.mainloop()
