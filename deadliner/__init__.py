# import the main window object (mw) from aqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo, qconnect
# import all of the Qt GUI library
from aqt.qt import *

from aqt import gui_hooks

from datetime import datetime

from typing import TYPE_CHECKING, Any, NewType
CardQueue = NewType("CardQueue", int)
QUEUE_TYPE_MANUALLY_BURIED = CardQueue(-3)
QUEUE_TYPE_SIBLING_BURIED = CardQueue(-2)
QUEUE_TYPE_SUSPENDED = CardQueue(-1)
QUEUE_TYPE_NEW = CardQueue(0)
QUEUE_TYPE_LRN = CardQueue(1)
QUEUE_TYPE_REV = CardQueue(2)
QUEUE_TYPE_DAY_LEARN_RELEARN = CardQueue(3)
QUEUE_TYPE_PREVIEW = CardQueue(4)

# Card types
CardType = NewType("CardType", int)
CARD_TYPE_NEW = CardType(0)
CARD_TYPE_LRN = CardType(1)
CARD_TYPE_REV = CardType(2)
CARD_TYPE_RELEARNING = CardType(3)

# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.

def refreshDeadliner() -> None:
    dm = DeadlineMgr()
    dm.refresh()
    mw.reset()

# create a new menu item, "test"
action = QAction("Refresh Deadliner", mw)
# set it to call testFunction when it's clicked
qconnect(action.triggered, refreshDeadliner)



# and add it to the tools menu
mw.form.menuTools.addAction(action)

class DeadlineMgr:
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        self._deadlines = None

    @property
    def deadlines(self):
        if not self._deadlines:
            self.refresh()
        return self._deadlines

    def refresh(self):
        self._deadlines = findDeadlines()

class DeadlineDb:
    CFG_KEY = "deadliner_cfg"
    def __init__(self):
        self.db = mw.col.get_config(DeadlineDb.CFG_KEY, default=None)
        if self.db:
            print("Found db:", self.db)
            self.version = self.db["version"]
            self.deadlines = self.db["deadlines"]
        else: # first time
            print("No db, creting one...")
            self.db = {"deadlines": {}, "version": 1}
            self.deadlines = {}


#    @property
#    def deadlines(self):
#        return self.db["deadlines"]

    def __repr__(self):
        return f"DeadlineDb(deadlines={self.deadlines})\t{self.db}"

    def save(self):
        self.db["deadlines"] = self.deadlines
        print("saving deadlines", self.db)
        mw.col.set_config(DeadlineDb.CFG_KEY, self.db)


class DeadlineDeck:


    def __init__(self, deck_id):
        self.deck_id = deck_id

        deck = mw.col.decks.get(deck_id)
        self.db = DeadlineDb()
        deck_key = str(deck_id)
        if deck_key in self.db.deadlines:
            self.cfg = self.db.deadlines[deck_key]
        else: # first time
            print(f"no cfg for this deck yet {self.deck_id}", self.db)
            dl = QDate.currentDate().addDays(7).toPyDate().strftime("%d-%m-%Y")
            self.cfg = {"enabled": True, "name": deck["name"], "deadline": dl}
            self.db.deadlines[deck_key] = self.cfg

        #self.cfg = mw.col.get_config(DeadlineDeck.CFG_KEY, default=None)

        #self.deadline = QDate.currentDate().addDays(7)

        self.name = self.cfg["name"]
        self.enabled = self.cfg["enabled"]
        self.deadline = self.cfg["deadline"]


    def __repr__(self):
        return f"DeadlineDeck(enabled={self.enabled},name={self.name},deadline={self.deadline})\t{self.cfg}"

    def save(self):
        self.cfg["name"] = self.name
        self.cfg["enabled"] = self.enabled
        self.cfg["deadline"] = self.deadline

        print("SavingDeck: ", self)
        self.db.save()


class DeadlinerDialog(QDialog):
    def __init__(self, deck_id):
        super().__init__(parent=mw)

        self.deadlineDeck = DeadlineDeck(deck_id)
        #logging.info("yoyoy")
        print("yoyoy")
        v_container = QVBoxLayout()
        self.setLayout(v_container)

        self.enabledButton = QCheckBox("Enable Deadline")
        self.enabledButton.setChecked(self.deadlineDeck.enabled)
        self.enabledButton.toggled.connect(self.onToggleEnable)

        self.gbox = QGroupBox("Deadline")
        #self.gbox_inner_layout = QVBoxLayout()
        #self.gbox.setLayout(self.gbox_inner_layout)

        self.form = QFormLayout()
        self.gbox.setLayout(self.form)
        #self.gbox_inner_layout.addWidget(self.form)

        self.nameEdit = QLineEdit(self.deadlineDeck.name)
        self.nameEdit.editingFinished.connect(self.onNameEdit)

        self.form.addRow(QLabel("Name:"), self.nameEdit)

        #date = QDate.currentDate().addDays(7)# Time.currentDateTime().addDays(7)
        self.deadlineDateEdit = QDateEdit(QDate.fromString(self.deadlineDeck.deadline, "dd-MM-yyyy"))
        self.deadlineDateEdit.dateChanged.connect(self.onDateEdit)
        self.form.addRow(QLabel("Deadline:"), self.deadlineDateEdit)

        v_container.addWidget(self.enabledButton)
        v_container.addWidget(self.gbox)


        # self.eventText.setMinimumWidth(150)
        # self.eventDate = QDateEdit(
        #     QDate.fromString(date, "yyyy-MM-dd"))
        #
        # self.saveButton = QPushButton("Save")
        # self.saveButton.clicked.connect(self.saveEvent)
        #
        # self.deleteButton = QPushButton("Delete")
        # self.deleteButton.clicked.connect(self.deleteEvent)
        #
        # layout.addWidget(self.eventText)
        # layout.addWidget(self.eventDate)
        # layout.addWidget(self.saveButton)
        # layout.addWidget(self.deleteButton)

    def closeEvent(self, event):
        self.onNameEdit()
        self.onDateEdit()
        print(f"Saving: {self.deadlineDeck}")
        self.deadlineDeck.save()
        refreshDeadliner()

    def onNameEdit(self):
        newName = self.nameEdit.text()
        self.deadlineDeck.name = newName
        print(f"edited: {newName}")
        pass

    def onDateEdit(self):
        newDate = self.deadlineDateEdit.date()
        self.deadlineDeck.deadline = newDate.toPyDate().strftime("%d-%m-%Y")
        print(f"edited: {newDate}")

    def onToggleEnable(self, enabled):
        self.deadlineDeck.enabled = enabled
        self.gbox.setDisabled(not enabled)
        # if enabled:
        #     showInfo("Enabled")
        #     #self.enabledButton.setChecked(True)
        #     #return True
        # else:
        #     showInfo("Disabled")


def open_deadliner_dialog(deck_id=None):
    dialog = DeadlinerDialog(deck_id)
    dialog.show()

def on_deck_browser_will_show_options_menu(menu, deck_id):
    action = menu.addAction("Edit Deadline")
    action.triggered.connect(lambda _, deck_id=deck_id: open_deadliner_dialog(deck_id))

from aqt.gui_hooks import deck_browser_will_show_options_menu
deck_browser_will_show_options_menu.append(on_deck_browser_will_show_options_menu)



# get this add-on's root directory name
addon_package = mw.addonManager.addonFromModule(__name__)

config = mw.addonManager.getConfig(__name__)

base_url = "/_addons/{}".format(addon_package)

class DeadlineStats:

    def __init__(self, deck_id, name, deadline):
        print(deck_id, name, deadline)
        self.name = name
        self.deck_id = deck_id
        self.deadline = datetime.strptime(deadline, "%d-%m-%Y").date()
        today = QDate.currentDate().toPyDate()

        self.daysLeft = (self.deadline-today).days

        #self.newLeft = self.new_cards_in_deck(deck_id)

        avg_reps, avg_sec = self.get_train_stats(deck_id)

        #self.get_day_stats()

        stats = mw.col.stats()

        dl = stats._limit()
        print("deck limit", dl)

        mature, young, new, _ = self.count_cards()
        print(f"mature: {mature}, young: {young}, new: {new}")
        denom = mature + young + new
        if denom > 0:
            self.progress = mature / (mature + young + new)
        else:
            self.progress = 0

        todo = young + new
        total_reps = todo * avg_reps
        total_time = total_reps * avg_sec
        print(f"need for {todo} at least {int(total_reps)} reps (each with {avg_sec:3.2f}s which takes {total_time/60:.1f}min")

        self.todoLearnN = todo
        if self.daysLeft != 0:
            self.todoReps = int(total_reps/self.daysLeft)
            self.todoTime = total_time/self.daysLeft/60 #min
        else:
            self.todoReps = int(total_reps)
            self.todoTime = total_time/60 #min
            
        print(f"Per day: reps: {self.todoReps} time: {self.todoTime} min")

    def get_day_stats(self):
        stats = mw.col.stats()
        (daysStud, fstDay) = stats._daysStudied()

        period = stats._periodDays()

        unit = "minutes"
        studied = daysStud
        start, days, chunk = stats.get_start_end_chunk()
        data = stats._done(days, chunk)
        (timdata, timsum) = stats._splitRepData(
            data,
            (
                (8, "", "Mature"),
                (7, "", "Young"),
                (9, "", "Relearn"),
                (6, "", "Learn"),
                (10, "", "Cram"),
            ),
        )

        tot = timsum[-1][1]
        print(f"studied: {studied} period: {period}")
        print( "Average for days studied", stats._avgDay(tot, studied, unit))
        print("If you studied every day", stats._avgDay(tot, period, unit))


        x = stats._periodDays()
        print("pd: ", x)

    def count_cards(self):
        deckChildren = [
            childDeck[1] for childDeck in mw.col.decks.children(self.deck_id)
        ]
        deckChildren.append(self.deck_id)
        deckIds = "(" + ", ".join(str(did) for did in deckChildren) + ")"

        return mw.col.db.first(
                f"""
    select
    sum(case when queue={QUEUE_TYPE_REV} and ivl >= 21 then 1 else 0 end), -- mtr
    sum(case when queue in ({QUEUE_TYPE_LRN},{QUEUE_TYPE_DAY_LEARN_RELEARN}) or (queue={QUEUE_TYPE_REV} and ivl < 21) then 1 else 0 end), -- yng/lrn
    sum(case when queue={QUEUE_TYPE_NEW} then 1 else 0 end), -- new
    sum(case when queue<{QUEUE_TYPE_NEW} then 1 else 0 end) -- susp
    from cards where did in {deckIds}"""
            )

    def get_train_stats(self, deck_id):
        deckChildren = [
            childDeck[1] for childDeck in mw.col.decks.children(self.deck_id)
        ]
        deckChildren.append(self.deck_id)
        deckIds = "(" + ", ".join(str(did) for did in deckChildren) + ")"
        n_cards, avg_reps, avg_sec = mw.col.db.first(
            f"""
            with train_stats as (select cid, count(*) as n_learn, sum(time) as t_learn FROM   revlog 
                     WHERE  cid IN (select cards.id from cards where did in {deckIds} and (type=1 or type=2)) group by cid)
					 select count(*), avg(n_learn), avg(t_learn)/1000 from train_stats""")

        print(f"train_stats: {self.deck_id} n_cards:{n_cards} avg_reps: {avg_reps}, avg_sec:{avg_sec}")

        return avg_reps, avg_sec



def findDeadlines():
    print("N decks:", mw.col.decks.count())
    #for deck in mw.col.decks.all_names_and_ids():
    #    print(deck.id)

    db = DeadlineDb()
    print("has: ", db)

    print("Calc deadlines")
    return [DeadlineStats(int(k), v["name"], v["deadline"]) for k,v in db.deadlines.items() if v['enabled']]



def display_footer(deck_browser, content):
    dm = DeadlineMgr()
    deadlines = dm.deadlines
    has_deadlines = len(deadlines) > 0

    res = """<br><br><link rel="stylesheet" type="text/css" href="{}/styles.css"/><h3 style="display: inline-block;margin: 0 20px" >Deadlines</h3>
    <div class="settings-btn" onclick='pycmd(\"refreshDeadliner\");'>
    <!--
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width=24 height=24>
    <path d="M142.9 142.9c62.2-62.2 162.7-62.5 225.3-1L327 183c-6.9 6.9-8.9 17.2-5.2 26.2s12.5 14.8 22.2 14.8H463.5c0 0 0 0 0 0H472c13.3 0 24-10.7 24-24V72c0-9.7-5.8-18.5-14.8-22.2s-19.3-1.7-26.2 5.2L413.4 96.6c-87.6-86.5-228.7-86.2-315.8 1C73.2 122 55.6 150.7 44.8 181.4c-5.9 16.7 2.9 34.9 19.5 40.8s34.9-2.9 40.8-19.5c7.7-21.8 20.2-42.3 37.8-59.8zM16 312v7.6 .7V440c0 9.7 5.8 18.5 14.8 22.2s19.3 1.7 26.2-5.2l41.6-41.6c87.6 86.5 228.7 86.2 315.8-1c24.4-24.4 42.1-53.1 52.9-83.7c5.9-16.7-2.9-34.9-19.5-40.8s-34.9 2.9-40.8 19.5c-7.7 21.8-20.2 42.3-37.8 59.8c-62.2 62.2-162.7 62.5-225.3 1L185 329c6.9-6.9 8.9-17.2 5.2-26.2s-12.5-14.8-22.2-14.8H48.4h-.7H40c-13.3 0-24 10.7-24 24z"/>
    </svg> -->
    </div>""".format(
        base_url, base_url)

    if has_deadlines:
        res += """<table cellspacing="6">
        <tr>
    <th>Name</th>
    <th>Days left</th>
    <th>To learn</th>
    <th>daily Cards</th>
    <th>daily study time</th>
    <th>Progress</th>
        </tr>
        """
        for dl in sorted(deadlines, key=lambda x: x.daysLeft):
            name = dl.name
            date = dl.deadline
            #content.stats += f"<p>Deadline: {name} - {date} -{dl.daysLeft} days Left to learn: {dl.todoLearnN} daily reps: {dl.todoReps} daily time: {dl.todoTime}</p>"
            res += f"""
            <tr>
            <td class="col1">{dl.name:s}</td>
            <td class="col2 days">{dl.daysLeft:d} days</td>
            <td class="col2 days">{dl.todoLearnN:d} cards</td>
            <td class="col3 percent">{dl.todoReps} cards/day</td>
            <td class="col3 percent">{dl.todoTime:.1f} min/day</td>
            <td class="col3 percent">{dl.progress:.1%}</td>
        </tr>
        <tr>
            <td colspan="6"><hr /></td>
        </tr>
            """

        res += """</table>"""
    else:
        res += "<p>No upcoming deadlines!</p>"

    content.stats += res

gui_hooks.deck_browser_will_render_content.append(display_footer)