from pprint import pprint
import sublime
import sublime_plugin


def get_region_under_last_cursor(view):
    word_to_find = view.sel()[-1]
    region = view.word(word_to_find)
    return region


def check_if_full_word(view, region):
    # checks if the region covers the full word
    return view.word(region).size() == region.size()


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
        # any partial matches i.e. print in pprint
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
    def filter_out_non_full_words(self, view, regions, word):
        # Looks at each region and determins if
        pass

    def want_event(self):
        print("in event")
        return False

    def run(self, edit):
        # Outline for this
        # get current selection then clear it?
        # get the last word in our selection
        # find all regions containing that worD
        # filter out comments or strings
        # add all remaining regions as a draw_no_fill
        # re add the previous selections...if they are in the filtered regions?
        # add the next region to the selection
        self.view.erase_regions("next_word")
        # pprint(self.view.symbols())
        # basing the rest of the decisions on the last selection we have.
        # Seems to be in line with how sublime does it natively.
        anchor_selection = self.view.sel()[-1]
        print(anchor_selection)
        print(anchor_selection)

        # Add to the final selections depending on
        final_selections = []

        if anchor_selection.size() == 0:
            # if the selection does not have a size, then we need to expand
            # the seleciton to the full word
            starting_selection = self.view.word(anchor_selection)
            selecting_full_word = True
        else:
            # Else, take the full selection and treat that as the word
            starting_selection = anchor_selection
            selecting_full_word = False

        print("word " + str(starting_selection) + " |")
        print(self.view.substr(starting_selection))

        # check if the button was pressed while not over a word
        # TOOD: Should allow spaces?
        if starting_selection.size() == 0 or self.view.substr(starting_selection).isspace():
            print("nada")
            return

        current_selections = [s for s in self.view.sel()]
        print("Current selctions")
        pprint(current_selections)

        print(starting_selection)
        selectionText = self.view.substr(starting_selection)
        print(selectionText)
        regions = self.view.find_all(selectionText, flags=sublime.LITERAL)

        current_selection_idx = 0
        for idx, region in enumerate(regions):
            if region == starting_selection:
                current_selection_idx = idx
                next_selection_idx = (idx + 1) % len(regions)
                break
        pprint(regions)
        print("Idx %s" % idx)

        # TODO: Could be more efficient and more concise
        # self.view.sel().clear()
        filtered_regions = []
        for region in regions:
            if not keep_region(self.view, region, selecting_full_word):
                continue
            filtered_regions.append(region)

        next_selection = regions[next_selection_idx]
        print("here")
        pprint(next_selection)

        # TODO: This is so wrong it's not even funny, but it'll work for the moment
        if selecting_full_word:
            final_regions = [starting_selection]
        else:
            # TODO: This is where we need to handle looping back
            final_regions = [starting_selection, next_selection]

        pprint(filtered_regions)
        for selection in current_selections:
            if selection in filtered_regions:
                final_regions.append(selection)
                print("yay")

        pprint(final_regions)

        self.view.add_regions("next_word", filtered_regions, "comment", flags=sublime.DRAW_NO_FILL)
        self.view.sel().add_all(final_regions)
        # self.view.add_regions("next_word", filtered_regions, "comment", flags=sublime.DRAW_NO_FILL)

        print("end")
