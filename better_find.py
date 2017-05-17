from functools import reduce
import sublime
import sublime_plugin

REGION_KEY = "find_region"


def check_if_full_word(view, region):
    # checks if the region covers the full word
    return view.word(region).size() == region.size()


def check_if_any_scope(full_scope_string, filtered_scopes):
    """returns true if any of the scopes passed in are in the full scope string"""
    return reduce(lambda acc, scope: acc + sublime.score_selector(full_scope_string, scope),
                  filtered_scopes, 0)


def has_region(view, region_name):
    return bool(view.get_regions(region_name))


def keep_region(view, region, selecting_full_word, scope_filters=["comment", "string"]):
    keep = True
    if selecting_full_word:
        # if we are selecting the full word, make sure we didn't get partial matches
        # like pprint when searching for print
        keep = check_if_full_word(view, region)

    scope = view.scope_name(region.b)

    return keep and not check_if_any_scope(scope, scope_filters)


def set_first_selection(view, region):
    view.settings().set('start_sel', (region.a, region.b))


def get_first_selection(view):
    sel = view.settings().get('start_sel', (view.sel()[0].a, view.sel().b))
    return sublime.Region(sel[0], sel[1])


def del_first_selection(view):
    view.settings().erase('start_sel')


# TODO: I only ever need the idx right?
def set_next_sel(view, region, next_idx):
    view.settings().set('next_sel', {"next_region": (region.a, region.b),
                                     "next_region_idx": next_idx})


def del_next_sel(view):
    view.settings().erase('next_sel')


def get_next_sel(view):
    sel = view.settings().get('next_sel')
    return sublime.Region(sel["next_region"][0], sel["next_region"][1]), sel["next_region_idx"]


class BetterFindNext(sublime_plugin.TextCommand):
    def start(self, excluded_scopes):
        """Starts the better find next operation

        Uses the last selection (i.e. the furthest down the file) as the word to
        start searching for. If the selection is empty, then it searches for the
        full word under the cursor, if not, it takes the selection as is.

        Main purpose is to setup the filtered regions so calls to add_next just
        go to the next selection
        """
        anchor_selection = self.view.sel()[-1]

        starting_selection = self.view.word(anchor_selection)
        selecting_full_word = True

        # check if the button was pressed while not over a word
        if starting_selection.size() == 0 or self.view.substr(starting_selection).isspace():
            return

        set_first_selection(self.view, starting_selection)

        selectionText = self.view.substr(starting_selection)
        regions = self.view.find_all(selectionText, flags=sublime.LITERAL)

        filtered_regions = []
        for region in regions:
            if not keep_region(self.view, region, selecting_full_word):
                continue
            filtered_regions.append(region)

        for idx, region in enumerate(filtered_regions):
            if region == starting_selection:
                next_selection_idx = (idx + 1) % len(filtered_regions)
                next_selection = filtered_regions[next_selection_idx]

        set_next_sel(self.view, next_selection, next_selection_idx)

        self.view.add_regions(REGION_KEY, filtered_regions, "source")
        self.view.sel().add(starting_selection)

    def add_next(self):
        sel, idx = get_next_sel(self.view)

        # scroll the view to the next selection
        self.view.show(sel)
        regions = self.view.get_regions(REGION_KEY)

        # TODO: Check the shit first
        self.view.sel().add(regions[idx])
        idx = (idx + 1) % len(regions)
        set_next_sel(self.view, regions[idx], idx)

    def run(self, edit, action="", excluded_scopes=["comment", "string"]):

        # I don't like enforcing the context parameters on users, it may not
        # be straightforward.
        if action == "":
            action = self.determine_action_from_context()

        if action == "start":
            self.start(excluded_scopes)
        elif action == "add_next":
            self.add_next()
        else:
            print("Action not found")

    def determine_action_from_context(self):
        sels = self.view.sel()
        if len(sels) == 1 and len(sels[0]) == 0:
            return "start"

        if has_region(self.view, REGION_KEY):
            return "add_next"


class ClearBetterFindSelection(sublime_plugin.TextCommand):
    def run(self, edit):
        # TODO: Go back to starting selection maybe?
        if len(self.view.sel()) == 1:
            single_selection = self.view.sel()[0]
            end = single_selection.end()
            single_selection.a = end - 1
            single_selection.b = end - 1
            self.view.sel().subtract(self.view.sel()[0])
            self.view.sel().add(single_selection)

        self.view.erase_regions(REGION_KEY)


class BetterFindNextEventListener(sublime_plugin.ViewEventListener):
    def on_query_context(self, key, operator=None, operand=None, match_all=False):
        if key == "has_region" and operand:
            return has_region(self.view, operand)

    def on_selection_modified_async(self):
        # TODO: Need to intelligently remove the regions if they exist
        if has_region(self.view, REGION_KEY) and self.view.sel()[0].empty():
            self.view.erase_regions(REGION_KEY)
