from functools import partial
from tars.commands.gib import Gib


def test_bracketify():
    qubr = partial(
        Gib.bracketify, opening=(r"\"\b", "\""), closing=(r"\b[.!?]*\"", "\"")
    )
    assert qubr('aaa') == 'aaa'
    assert qubr('"aaa"') == '"aaa"'
    assert qubr('"aaa bbb"') == '"aaa bbb"'
    assert qubr('"aaa') == '"aaa"'
    assert qubr('aaa"') == '"aaa"'
    assert qubr('"aaa" "bbb') == '"aaa" "bbb"'
    assert qubr('aaa" "bbb"') == '"aaa" "bbb"'
    assert qubr('aaa" bbb') == '"aaa" bbb'
    assert qubr('aaa "bbb') == 'aaa "bbb"'
    assert qubr('"aaa "bbb') == '"aaa "bbb""'
    assert qubr('aaa!') == 'aaa!'
    assert qubr('"aaa!"') == '"aaa!"'
    assert qubr('"aaa! bbb!"') == '"aaa! bbb!"'
    assert qubr('"aaa!') == '"aaa!"'
    assert qubr('aaa!"') == '"aaa!"'
    assert qubr('"aaa!!!" "bbb!') == '"aaa!!!" "bbb!"'
    assert qubr('aaa!!" "bbb!!"') == '"aaa!!" "bbb!!"'
    assert qubr('aaa!!!" bbb') == '"aaa!!!" bbb'
    assert qubr('aaa "!bbb') == 'aaa "!bbb'
    pabr = partial(Gib.bracketify, opening=(r"\(", "("), closing=(r"\)", ")"))
    assert pabr('aaa') == 'aaa'
    assert pabr('(aaa)') == '(aaa)'
    assert pabr('(aaa bbb)') == '(aaa bbb)'
    assert pabr('(aaa') == '(aaa)'
    assert pabr('aaa)') == '(aaa)'
    assert pabr('(aaa) (bbb') == '(aaa) (bbb)'
    assert pabr('aaa) (bbb)') == '(aaa) (bbb)'
    assert pabr('aaa) bbb') == '(aaa) bbb'
    assert pabr('aaa (bbb') == 'aaa (bbb)'
    assert pabr('aa((((aa') == 'aa((((aa))))'
