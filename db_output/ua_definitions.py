# this will hold actions, event types etc
# TODO (soon) build checking + adding against this in parse


# from Thunder2018_AllGames
KNOWN_ACTIONS = ['Pull', 'Throwaway', 'Catch', 'Goal', 'D', 'Drop', 'PullOb', 'Stall', 'EndOfFirstQuarter', 'Callahan']

RECEIVING_ACTIONS = ['Catch', 'Goal', 'Drop']

TURNOVERS = ['Stall', 'Drop', 'Throwaway']

PASSES = ['Catch', 'Goal', 'Throwaway', 'Drop']

CATCHES = ['Catch', 'Goal']

PULLS = ['Pull', 'PullOB']

BLOCKS = ['D', 'Callahan']

GOALS = ['Goal']

CALLAHANS = ['Callahan']

# Event Type refers to our O/D status when the event occurred (or break in play)

EVENT_TYPES = ['Offense', 'Defense', 'Cessation']

BREAK_TYPES = ['Cessation']

POSSESSION_TYPES = ['Offense', 'Defense']
