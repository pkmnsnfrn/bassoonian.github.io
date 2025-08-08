[Figma](https://www.figma.com/design/S0CSryxWlZRtJxW2e8IYcW/Untitled?node-id=0-1&p=f&viewport=713%252C526%252C1.76&t=x3gl8uGvGbhzOz1K-0)

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

# HIERARCHY
* Stages
    * Information (Static List)
        * Pronounciation
        * Allophony
        * Orthography
    * Sound Changes
* Morphology
    * Stage Data
    * Nominal - Noun (Dynamic List)
    * Nominal - Pronoun
    * Nominal - Adjective
    * Nominal - Verbal
* Lexicon (Dynamic List)
    * Letters
* Corpus
* Sources
* Extra Functions
    * Statistics
    * Todo
    * Warnings
    * Meta Information

# Stage Selector
The stage selector is a floating box in the top left hand of the screen. All of the created stages are listed as tags in the box. If the number of stages is greater than the number of stages that can be displayed in two rows, the third row will show a fade gradient over the third row, indicating there are more stages.

If the number of stages is greater than the number of stages that can be displayed in two rows, a search box will appear above the first stage. Typing in the searchbox will remove all the stages from the list that do not fuzzy match the query - this should update on every keystroke. Clicking the x on the searchbox will clear the query in the search box.

Clicking on any of the stages will change the program to be editing this stage. Clicking on a stage that is currently selected does nothing.

# Main Menu
The main menu lists all the different pages that can be found in the program. Each item in the menu can be clicked to switch to that page. The keyboard shortcut listed to the right of the menu item's name will also trigger a switch to that page. When a page is being currently viewed, it is highlighted. Clicking on a page that is already being viewed does nothing.

# Stage List
The screen is filled with a table of all the existing stages. The stages are listed in their order, with the oldest stage at the top.

Clicking the Add button will add a stage AFTER the row where the button was clicked. For example, if the button was clicked on Row 2, the new stage will be added in Slot 3.

Clicking and holding the icon on the left side of the row allows users to reoreder stages by dragging them up or down.

Clicking anywhere else on the stage's row will open the Stage Information page.

## Stage Information 

Lorem

# Static List

# Dynamic List

# Regex Editor

# Linker

# Edit List
