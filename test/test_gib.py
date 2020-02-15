from functools import partial
from commands.gib import gib

def test_bracketify():
    qubr = partial(gib.bracketify,
                   opening=("\"", r"\"\b"),
                   closing=("\"", r"\b[.!?]*\""))
    assert qubr('aaa') == 'aaa'
    assert qubr('"aaa"') == '"aaa"'
    assert qubr('"aaa bbb"') == '"aaa bbb"'
    assert qubr('"aaa') == '"aaa"'
    assert qubr('aaa"') == '"aaa"'
    assert qubr('"aaa" "bbb') == '"aaa" "bbb"'
    assert qubr('aaa" "bbb"') == '"aaa" "bbb"'
    assert qubr('aaa" bbb') == '"aaa" bbb'
    assert qubr('aaa "bbb') == 'aaa "bbb"'
    # TODO punctuation
