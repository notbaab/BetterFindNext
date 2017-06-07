from functools import reduce
import sublime
import sublime_plugin
import logging

REGION_KEY = "find_region"
logger = logging.getLogger(__name__)


def check_if_full_word(view, region):
    # checks if the region covers the full word
    return view.word(region).size() == region.size()


def check_if_any_scope(full_scope_string, filtered_scopes):
    """returns true if any of the scopes passed in are in the full scope string"""
    return reduce(lambda acc, scope: acc + sublime.score_selector(full_scope_string, scope),
                  filtered_scopes, 0)


def recalculate_find_next_region(view):
    """Resizing will only work if every selection is the same, else it removes the regions
    """
    selections = view.sel()
    previous_selection = view.substr(selections[0])
    for selection in selections:
        if previous_selection != view.substr(selection):
            # nothing matches, fuck it erase it
            view.erase_regions(REGION_KEY)
            return

    # so the selections are the same, get the next selection and shrink it
    # down to the new selection size and reduce the find next region
    regions = view.get_regions(REGION_KEY)
    idx = get_next_sel_idx(view)
    next_selection = regions[idx]

    new_size = selections[0].size()
    new_regions = []

    for region in regions:
        new_region = sublime.Region(region.begin(), region.begin() + new_size)
        new_regions.append(new_region)

        if next_selection.intersects(region):
            set_next_sel_idx(view, idx)

    view.erase_regions(REGION_KEY)
    view.add_regions(REGION_KEY, new_regions, "source")


def has_region(view, region_name):
    return bool(view.get_regions(region_name))


def find_index_of_selection(regions, selection):
    next_selection_idx = None

    for idx, region in enumerate(regions):
        if region == selection:
            next_selection_idx = (idx + 1) % len(regions)

    return next_selection_idx


def filter_regions(view, regions, selecting_full_word, starting_selection, scope_filters):
    filtered_regions = []

    for region in regions:
        if not keep_region(view, region, selecting_full_word, scope_filters):
            continue
        filtered_regions.append(region)

    return filtered_regions


def keep_region(view, region, selecting_full_word, scope_filters):
    keep = True
    if selecting_full_word:
        # if we are selecting the full word, make sure we didn't get partial matches
        # like pprint when searching for print
        keep = check_if_full_word(view, region)

    scope = view.scope_name(region.begin())

    return keep and not check_if_any_scope(scope, scope_filters)


def set_first_selection(view, region):
    view.settings().set('start_sel', (region.a, region.b))


def get_first_selection(view):
    sel = view.settings().get('start_sel', (view.sel()[0].a, view.sel()[0].b))
    return sublime.Region(sel[0], sel[1])


def del_first_selection(view):
    view.settings().erase('start_sel')


def set_next_sel_idx(view, next_idx):
    view.settings().set('next_sel', {"next_region_idx": next_idx})


def del_next_sel(view):
    view.settings().erase('next_sel')


def get_next_sel_idx(view):
    sel = view.settings().get('next_sel')
    return sel["next_region_idx"]


class Testing(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase_regions("other")
        point = self.view.sel()[-1].end()
        region = [self.view.extract_scope(point)]
        self.view.add_regions("other", region, "source")


class BetterFindNext(sublime_plugin.TextCommand):
    def start(self, excluded_scopes, expand_selection_to_word):
        """Starts the better find next operation

        Uses the last selection (i.e. the furthest down the file) as the word to
        start searching for. If the selection is empty, then it searches for the
        full word under the cursor, if not, it takes the selection as is.

        Main purpose is to setup the filtered regions so calls to add_next just
        go to the next selection
        """
        starting_selection = self.view.sel()[-1]

        if expand_selection_to_word:
            starting_selection = self.view.word(starting_selection)

        # check if the button was pressed while not over a word
        if starting_selection.size() == 0 or self.view.substr(starting_selection).isspace():
            return

        set_first_selection(self.view, starting_selection)

        selectionText = self.view.substr(starting_selection)
        regions = self.view.find_all(selectionText, flags=sublime.LITERAL)

        filtered_regions = filter_regions(self.view, regions, expand_selection_to_word,
                                          starting_selection, excluded_scopes)

        next_selection_idx = find_index_of_selection(filtered_regions, starting_selection)

        set_next_sel_idx(self.view, next_selection_idx)

        self.view.add_regions(REGION_KEY, filtered_regions, "source")
        self.view.sel().add(starting_selection)

    def add_next(self):
        regions = self.view.get_regions(REGION_KEY)
        idx = get_next_sel_idx(self.view)
        next_sel = regions[idx]

        # scroll the view to the next selection
        self.view.show(next_sel)

        # TODO: Check to make sure that a new region exists
        self.view.sel().add(regions[idx])

        idx = (idx + 1) % len(regions)
        set_next_sel_idx(self.view, idx)

    def run(self, edit, action="", excluded_scopes=["comment", "string"]):
        # I don't like enforcing the context parameters on users, we technically
        # can determine them ourselves
        if action == "":
            action = self.determine_action_from_context()

        if action == "start_full_word":
            self.start(excluded_scopes, True)
        elif action == "start_partial_selection":
            self.start(excluded_scopes, False)
        elif action == "add_next":
            self.add_next()
        else:
            logger.error("Action %s not found", action)

    def determine_action_from_context(self):
        sels = self.view.sel()

        # Add next should resolve first
        if has_region(self.view, REGION_KEY):
            return "add_next"

        # TODO: Do we only want to allow starting when a single cursor is there? We can do it
        # like the default ctrl+d and just start looking for the lowest selection and keep the
        # mismatched ones. That may get convoluted though...
        single_selection = len(sels) == 1
        empty_selection = len(sels[-1]) == 0

        if single_selection:
            if empty_selection:
                return "start_full_word"
            else:
                return "start_partial_selection"


class ClearBetterFindSelection(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.erase_regions(REGION_KEY)
        if len(self.view.sel()) != 1:
            new_selections = []
            for sel in self.view.sel():
                end = sel.end()
                sel.a = end - 1
                sel.b = end - 1
                new_selections.append(sel)
            self.view.sel().clear()
            self.view.sel().add_all(new_selections)
        else:
            # Not needed if command is mapped to escape but no harm in running it twice
            self.view.run_command("single_selection")


class BetterFindNextEventListener(sublime_plugin.ViewEventListener):
    def on_query_context(self, key, operator=None, operand=None, match_all=False):
        if key == "has_region" and operand:
            return has_region(self.view, operand)

    def applies_to_primary_view_only():
        return False

    def on_selection_modified_async(self):
        # TODO: Need to intelligently remove the regions if they exist
        if has_region(self.view, REGION_KEY):
            cursor = self.view.sel()[0]
            if cursor.empty():
                self.view.erase_regions(REGION_KEY)
                return

            if cursor.size() != get_first_selection(self.view).size():
                recalculate_find_next_region(self.view)
