# Goals

Build a UI to interface with data in a way that exports a website

# Stages
- Easily switch between stages of the language on the fly (top level control?)
- Newer stages need to inherit everything from old stages (each "element") needs to be tagged with the originating stage 
- Stage 0 will have a lot of functionality disabled

## Stage Information
- Each stage has regex rules for Pronounciation, Allophony and Orthography
- All the words in a stage inheirit the regex rules for that specific stage
- Regex rules need to be easily reordered / added / dropped and swapped, with a live updater of what a target word looks like afterwards with a test word field

## Stage Sounds Changes
- Stage 0 does not need sound changes
- Stage X takes the word from Stage X-1 and applies the sound changes from X to it
- Stage Y takes the word from Stage X-1 and applies the sound changes from X to it, and then Y
- Needs to use the same rule ordering engine

### Sound Change Schema
- Regex rules (use the regex ordering engine)
- Prose (large text field)
- Chapter Name (short text)
- Internal notes (large text)
- Recursion (checkbox)
- Odds (slider, default 100
- Sound changes should default to locked but have a button to edit with a modal asking to confirm

# Morphology
- Grammar for a language but doesn't have a syntax...?
- Some morphology only applies to Stage 0 (denoted with *)
- Each morphology entry has different types of data to be stored

## Stage Level
Which numbers and genders do the morphologies change for? These directly influence the row and column headers for the tables. What are the pronoun cases? What are the noun cases?

## Nominal - Noun*
Needs to track name, abbreviation, gender (from a list), table for inheirited number and case, and table for override number and case

## Nominal - Pronoun*
Needs to track name, abbreviation, table for inheirited number and case, and table for override number and case

## Nominal - Adjective*
Name, abbreviation, same table for inheirted number and case and table for override number and case

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
- Part of speech / speech class
    - Noun  
    - Pronoun  
    - Adjective  
    - Verb  
    - Adverb  
    - Adposition  
    - Root  
    - Affix  
    - Particle  
    - Conjunction  
- Inflection pattern ???
- Internal notes (markdown)
- Prose (long text) 
- Sources (link existing or add new)
- Origin (cannot be edited and must be selected first)
    - Inheirtance
    - Derivation (comes with mandatory text box)
    - Loan (comes with optional text box)
    - Ex-nililo (comes with optional text box and checkbox for scientifically sourced)
- Undergoes sporadic sound changes
    - Lists all sound changes for this stage, and if the odds are 100%, it is checked and locked, otherwise unchecked

# Corpus
- Glossary of documents that shows how the language is actually built
- Each document has a title and text, and has an edit for a markdown field

# Sources
- Each source has the following
    - name
    - authors
    - publication year
    - reference
    - link
- Users can edit or add existing sources
- Needs to show the number of times this source has been cited

# Extra Functions
- Statistics
- Todo
- Warnings
- Meta Information
