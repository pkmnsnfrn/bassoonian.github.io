# Goals

Build a UI to interface with data in a way that exports a website

# Stages
- Easily switch between stages of the language on the fly (top level control?)
- Newer stages need to inherit everything from old stages (each "element") needs to be tagged with the originating stage 
- Stage 0 will have a lot of functionality disabled

## Stage Information
- Each stage has regex rules for Pronounciation, Allophony and Orthography
- All the words in a stage inheirit the regex rules for that specific stage
- Regex rules need to be easily reordered / added / dropped and swapped, with a live updater of what a target word looks like afterwards

## Stage Sounds Changes
- Stage 0 does not need sound changes
- Stage X takes the word from Stage X-1 and applies the sound changes from X to it
- Stage Y takes the word from Stage X-1 and applies the sound changes from X to it, and then Y
- Needs to use the same rule ordering engine

### Sound Change Schema
- Regex rule itself
- Prose (large markdown field)
- Chapter Name (short markdown)
- Internal notes (large markdown)
- Recursion (checkbox)
- Odds (slider, default 100

# Morphology
- Grammar for a language but doesn't have a syntax...?
- Some morphology only applies to Stage 0 (denoted with *)
- Each morphology entry has different types of data to be stored

## Nominal - Noun
- Inflection point
* Nominal - Noun
* Nominal - Pronoun
* Nominal - Adjective
* Verbal

## Stage Level
Which numbers and genders do the morphologies change for? These directly influence the row and column headers for the tables. What are the pronoun cases? What are the noun cases?

## Nominal - Noun*
Needs to track name, abbreviation, gender (from a list), table for inheirited number and case, and table for override number and case

## Nominal - Pronoun*
Needs to track name, abbreviation, table for inheirited number and case, and table for override number and case

## Nominal - Adjective*
Name, abbreviation, and reference other nouns and pronouns

## Nominal - Verbal*
### Stage
What number of people does the verb change for?

Verbs need to be seen through the following axes
- Voice
- Mood
- TAM
- Tense / Aspect

## Lexicon
The dictionary of all the words
- Raw form (short text field)
- Raw form override 
- Meanings (short text field, multiple can be added per word)
- Part of speech
- Inflection pattern
- Internal notes
- Prose
- Sources





