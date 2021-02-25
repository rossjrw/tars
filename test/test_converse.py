from tars.commands.converse import find_acronym


def test_acronym_match():
    def acro(string, final=None):
        if final is None:
            final = string
        acronyms = find_acronym(string, "TARS")
        if acronyms is False:
            return False
        raw_acronym, _ = acronyms
        assert raw_acronym == final
        return True

    assert acro("T A R S")
    assert acro("because the angry rash spreads", "the angry rash spreads")
    assert acro("Totally Awesome Robot (/S)")
    assert acro("Total Annihilation Reigns Supreme")
    assert acro("Tool-Assisted Robotic Sassmouth")
    assert acro("Tell Aaron Rocks Suck")
    assert acro("TARS: A Recursive Semantic")
    assert acro("These Acronyms Really Suck")
    assert acro("Tales Are Real Shitty")
    assert acro("Tummy & Ass Rubs, Sergeant")
    assert acro("Thanks, Anderson Robotics. Sweet.")
    assert acro("Trying Acronyms Repeatedly? Super!")
    assert acro("The Angry Rash Spreads")
    assert acro("Talking Animals? *Rawr* *Snuggles*")
    assert acro("Tagliatelle And Ragù Sauce")
    assert acro("Toronto Activists: Really Sad")
    assert acro("Temperatures Are Rising - Sorry!")
    assert acro("Try And Run, Samuel.")
    assert acro("Tomorrow, Another Revolution Starts")
    assert acro("Three Anuses Rigorously Spread")
    assert acro("Tomorrow's A Recycled Sunday")
    assert acro("Trying And Rarely Succeeding")
    assert acro("Time And Relative... Space?")
    assert acro("Taunting A Random Stranger")
    assert acro("Tool-Assisted Run (Sexual%)")
    assert acro("'Tis A Riddle, See?")
    assert acro("Tear Ass, Riptide Sailor!")
    assert acro("This Anomaly Repeatedly Shits")
    assert acro("Transmogrification And Radical Sorcery")
    assert acro("n, n, T, A, R, S, n,", "T, A, R, S,")
    assert acro("terrific, another robotic sentience")
    assert acro("terrific another, robotic sentience")
