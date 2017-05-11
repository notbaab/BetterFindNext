from pprint import pprint
import sublime
import sublime_plugin

REGION_KEY = "find_region"


def get_region_under_last_cursor(view):
    word_to_find = view.sel()[-1]
    region = view.word(word_to_find)
    return region


def check_if_full_word(view, region):
    # checks if the region covers the full word
    return view.word(region).size() == region.size()


# TODO: Use match selector?
def check_if_any_scope(full_scope_string, scopes):
    # returns true if any of the scopes passed in are in the full scope string
    for scope in scopes:
        if scope in full_scope_string:
            return True

    return False


def has_region(view, key, operator=None, operand=None, match_all=False):
    regions = view.get_regions(operand)
    log.debug("query_context: regions")
    return bool(regions)


def keep_region(view, region, selecting_full_word, scope_filters=["comment", "string"]):
    keep = True
    if selecting_full_word:
        # if we are selecting the full word, make sure we didn't get partial matches
        # like pprint when searching for print
        keep = check_if_full_word(view, region)

    scope = view.scope_name(region.b)

    return keep and not check_if_any_scope(scope, scope_filters)


# TODO: This needs to be way smarter. If the region for finding things exists
# alredy, just add the next in the region, don't recompute everything again.
# The flow for that will be:
#       - Pull the current region
#       - If empty, go through the find process.
#       - else: add the next idx in the region to the selection?
class BetterFindNext(sublime_plugin.TextCommand):
    """
    """

    def start(self):
        anchor_selection = self.view.sel()[-1]

        starting_selection = self.view.word(anchor_selection)
        selecting_full_word = True

        # check if the button was pressed while not over a word
        # TOOD: Should allow spaces?
        if starting_selection.size() == 0 or self.view.substr(starting_selection).isspace():
            return

        selectionText = self.view.substr(starting_selection)
        regions = self.view.find_all(selectionText, flags=sublime.LITERAL)

        # TODO: Could be more efficient and more concise
        # filtered_regions
        filtered_regions = []
        for region in regions:
            if not keep_region(self.view, region, selecting_full_word):
                continue
            filtered_regions.append(region)

        pprint(filtered_regions)
        pprint(starting_selection)

        for idx, region in enumerate(filtered_regions):
            if region == starting_selection:
                next_selection_idx = (idx + 1) % len(filtered_regions)
                next_selection = filtered_regions[next_selection_idx]

        self.set_next_sel(next_selection, next_selection_idx)

        # next_selection = filtered_regions[next_selection_idx]
        # final_regions = [starting_selection]

        # for selection in current_selections:
        #     if selection in filtered_regions:
        #         final_regions.append(selection)

        self.view.add_regions(REGION_KEY, filtered_regions, "source")
        self.view.sel().add(starting_selection)
        self.view.show(self.view.sel()[-1])

    # TODO: I only ever need the idx right?
    def set_next_sel(self, region, next_idx):
        print("here")
        print(region)
        self.view.settings().set('next_sel', {"next_region": (region.a, region.b),
                                              "next_region_idx": next_idx})

    def del_next_sel(self):
        self.view.settings().erase('next_sel')

    def get_next_sel(self):
        sel = self.view.settings().get('next_sel')
        return sublime.Region(sel["next_region"][0], sel["next_region"][1]), sel["next_region_idx"]

    def run(self, edit, action="start"):
        if action == "start":
            self.start()
            return
        else:
            sel, idx = self.get_next_sel()
            regions = self.view.get_regions(REGION_KEY)
            # TODO: Check the shit first
            self.view.sel().add(regions[idx])
            idx = (idx + 1) % len(regions)
            self.set_next_sel(regions[idx], idx)
            print("got it")
            return


class ClearBetterFindSelection(sublime_plugin.TextCommand):
    def run(self, edit):
        if len(self.view.sel()) == 1:
            single_selection = self.view.sel()[0]
            end = single_selection.end()
            single_selection.a = end - 1
            single_selection.b = end - 1
            self.view.sel().subtract(self.view.sel()[0])
            self.view.sel().add(single_selection)

        self.view.erase_regions(REGION_KEY)


class BetterFindNextEventListener(sublime_plugin.EventListener):

    def on_query_context(self, view, key, operator=None, operand=None, match_all=False):
        if key == "has_region" and operand:
            log.debug("query_context %s: %s, %s, %s", key, operator, operand, match_all)
            return has_region(view, key, operator, operand, match_all)

    # def on_selection_modified(self, view):
    #     regions = view.get_regions(REGION_KEY)

    #     #     view.erase_regions(REGION_KEY)
