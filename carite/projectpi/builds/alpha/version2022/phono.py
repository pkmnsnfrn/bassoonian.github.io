def phonoInvToTable(inv):
    vowels_ipa = ["i", "y", "ɨ", "ʉ", "ɯ", "u", "ɪ", "ʏ", "ʊ", "e", "ø", "ɘ", "ɵ", "ɤ", "o", "ə", "ɛ", "œ", "ɜ", "ɞ", "ʌ", "ɔ", "æ", "ɐ", "a", "ɶ", "ä", "ɑ", "ɒ", "ū", "ȳ", "ī", "ā", "ē", "ō"]
    consonants = [
        [["m̥", "m"], ["" , "ɱ"], ["" , "n̼"], ["" , "" ], ["n̥", "n"], ["" , "" ], ["ɳ̊", "ɳ"], ["ɲ̊", "ɲ"], ["ŋ̊", "ŋ"], ["" , "ɴ"], ["" , "" ], ["" , "" ]],
        [["p", "b"], ["p̪", "b̪"], ["t̼", "d̼"], ["" , "" ], ["t", "d"], ["" , "" ], ["ʈ", "ɖ"], ["c", "ɟ"], ["k", "g"], ["q", "ɢ"], ["ʡ", "" ], ["ʔ", "" ]],
        [["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["s", "z"], ["ʃ", "ʒ"], ["ʂ", "ʐ"], ["ɕ", "ʑ"], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ]],
        [["ɸ", "β"], ["f", "v"], ["θ̼", "ð̼"], ["θ", "ð"], ["θ̠", "ð̠"], ["" , "" ], ["" , "" ], ["ç", "ʝ"], ["x", "ɣ"], ["χ", "ʁ"], ["ħ", "ʕ"], ["h", "ɦ"]],
        [["" , "w"], ["" , "ʋ"], ["" , "" ], ["" , "" ], ["" , "ɹ"], ["" , "" ], ["" , "ɻ"], ["" , "j"], ["" , "ɰ"], ["" , "" ], ["" , "" ], ["" , "ʔ̞"]],
        [["" , "" ], ["" , "ⱱ"], ["" , "ɾ̼"], ["" , "" ], ["ɾ̥", "ɾ"], ["" , "" ], ["ɽ̊", "ɽ"], ["" , "" ], ["" , "" ], ["" , "ɢ̆"], ["" , "ʡ̆"], ["" , "" ]],
        [["ʙ̥", "ʙ"], ["" , "" ], ["" , "" ], ["" , "" ], ["r̥", "r"], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["ʀ̥", "ʀ"], ["ʜ", "ʢ"], ["" , "" ]],
        [["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["ɬ", "ɮ"], ["" , "" ], ["ꞎ", "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ]],
        [["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "l"], ["" , "" ], ["" , "ɭ"], ["" , "ʎ"], ["" , "ʟ"], ["" , "ʟ̠"], ["" , "" ], ["" , "" ]],
        [["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["ɺ̥", "ɺ"], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ], ["" , "" ]]
    ]
    consonant_places = ["Bilabial", "Labiodental", "Linguolabial", "Dental", "Alveolar", "Postalveolar", "Retroflex", "Palatal", "Velar", "Uvelar", "Pharyngeal", "Glottal"]
    consonant_manners = ["Nasal", "Plosive", "Sibilan fricative", "Non-sibilant fricative", "Approximant", "Tap/flap", "Trill", "Lateral fricative", "Lateral approximant", "Lateral tap/flap"]
    consonants_in = []
    vowels = []
    # sort inventory into consonants and vowels
    for x in inv:
        if x[0] in vowels_ipa:
            vowels.append(x)
        else:
            consonants_in.append(x)
    # consonants: eliminate those not present
    for y in consonants:
        for x in y:
            if x[0] not in consonants_in:
                x[0] = ""
            if x[1] not in consonants_in:
                x[1] = ""
    print(vowels)
    print(consonants)

### dental + alveolar + postalveolar = coronal
### bilabial + labiodental = labial