from pprint import pprint
import sublime
import sublime_plugin


def get_region_under_last_cursor(view):
    word_to_find = view.sel()[-1]
    region = view.word(word_to_find)
    return region


class BetterFindNext(sublime_plugin.TextCommand):
    """
    """

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
        word = get_region_under_last_cursor(self.view)
        print("word " + str(word) + " |")
        print(self.view.substr(word))
        # return

        # check if the button was pressed while not over a word
        if word.size() == 0 or self.view.substr(word).isspace():
            print("nada")
            return

        current_selections = [s for s in self.view.sel()]
        pprint(current_selections)

        print(word)
        selectionText = self.view.substr(word)
        print(selectionText)
        regions = self.view.find_all(selectionText)
        pprint(regions)

        # self.view.sel().clear()
        filtered_regions = []
        for region in regions:
            scope = self.view.scope_name(region.b)
            if "comment" in scope or "string" in scope:
                continue
            # self.view.sel().add(region)
            filtered_regions.append(region)

        final_regions = []
        for selection in current_selections:
            if selection in filtered_regions:
                final_regions.append(selection)
                print("yay")

        self.view.add_regions("next_word", filtered_regions, "comment", flags=sublime.DRAW_NO_FILL)

        print("end")
