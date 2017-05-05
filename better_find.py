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


def keep_region(view, region, selecting_full_word, scope_filters=["comment", "string"]):
    keep = True
    if selecting_full_word:
        # if we are selecting the full word, make sure we didn't get
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

    def run(self, edit):
        anchor_selection = self.view.sel()[-1]
        self.view.erase_regions(REGION_KEY)

        if anchor_selection.size() == 0:
            # if the selection does not have a size, then we need to expand
            # the seleciton to the full word
            starting_selection = self.view.word(anchor_selection)
            selecting_full_word = True
        else:
            # Else, take the full selection and treat that as the word
            starting_selection = anchor_selection
            selecting_full_word = False

        # check if the button was pressed while not over a word
        # TOOD: Should allow spaces?
        if starting_selection.size() == 0 or self.view.substr(starting_selection).isspace():
            return

        current_selections = [s for s in self.view.sel()]

        selectionText = self.view.substr(starting_selection)
        regions = self.view.find_all(selectionText, flags=sublime.LITERAL)

        for idx, region in enumerate(regions):

                break

        # TODO: Could be more efficient and more concise
        # self.view.sel().clear()
        # filtered_regions
        filtered_regions = []
        for region in regions:
            if not keep_region(self.view, region, selecting_full_word):
                continue
            filtered_regions.append(region)

        for idx, region in enumerate(filtered_regions):
            if region == starting_selection:
                next_selection_idx = (idx + 1) % len(filtered_regions)

        next_selection = filtered_regions[next_selection_idx]

        # TODO: This is so wrong it's not even funny, but it'll work for the moment
        if selecting_full_word:
            final_regions = [starting_selection]
        else:
            # TODO: This is where we need to handle looping back
            final_regions = [starting_selection, next_selection]

        for selection in current_selections:
            if selection in filtered_regions:
                final_regions.append(selection)

        self.view.add_regions(REGION_KEY, filtered_regions, "source")
        self.view.sel().add_all(final_regions)
        self.view.show(self.view.sel()[-1])


# class ClearRegions(sublime_plugin.EventListener):

#     # def on_query_context(self, view, key, operator=None, operand=None, match_all=False):
#     #     if key == "has_region":
#     #         log.debug("query_context %s: %s, %s, %s", key, operator, operand, match_all)
#     #         if operand:
#     #             regions = view.get_regions(operand)
#     #             log.debug("query_context: regions")
#     #             return bool(regions)

#     def on_selection_modified(self, view):
#         regions = view.get_regions(REGION_KEY)
#         # if regions:
#         #     view.erase_regions(REGION_KEY)
