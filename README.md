# BetterFindNext

A find next plugin that (attempts to) understand code.


![Not found](add_next.gif)


BetterFindNext is aims to be a smarter version of the built in find_next (super+d) command. It achieves this by allowing the user to customize what scope gets ignored. 


## Default Key bindings and Behavior 

By default, the shortcut maps to `alt+i` and ignores adding strings or comments. 

## Ignore Options
The key binding accepts a list of scopes as it's `excluded_scopes` args. For Example, if you want to not include `constant` scope, you would define a mapping like so 
```json
[
    {"keys": ["ctrl+i"], "command": "better_find_next", "args": {"excluded_scopes": ["constant"]}},
]
```

In a very contrived example, this would produce behavior like this.

![Not found](filter_constants.gif)



## TODO
Requests can be submitted in the issues. Current plans are
- Limit find to current function 
- Limit find to current indentation 
- Allow included_scopes option (inverse of the current implementation) 

## Install
Search for BetterFindNext on Package Control