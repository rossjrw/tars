# cython: language_level=3

BEGIN = "___BEGIN__"
END = "___END__"

cdef cbuild(corpus, int state_size):
    model = {}

    for run in corpus:
        items = ([BEGIN] * state_size) + run + [ END ]
        for i in range(len(run) + 1):
            state = tuple(items[i:i+state_size])
            follow = items[i+state_size]
            if state not in model:
                model[state] = {}

            if follow not in model[state]:
                model[state][follow] = 0

            model[state][follow] += 1
    return model

def build(corpus, state_size):
    return cbuild(corpus, state_size)
