[Figma](https://www.figma.com/design/S0CSryxWlZRtJxW2e8IYcW/Untitled?node-id=0-1&p=f&viewport=713%252C526%252C1.76&t=x3gl8uGvGbhzOz1K-0)

# Goals

Build a UI to interface with data in a way that exports a website

# Stage Selector
The stage selector is a floating box in the top left hand of the screen. All of the created stages are listed as tags in the box. If the number of stages is greater than the number of stages that can be displayed in two rows, the third row will show a fade gradient over the third row, indicating there are more stages.

If the number of stages is greater than the number of stages that can be displayed in two rows, a search box will appear above the first stage. Typing in the searchbox will remove all the stages from the list that do not fuzzy match the query - this should update on every keystroke. Clicking the x on the searchbox will clear the query in the search box.

Clicking on any of the stages will change the program to be editing this stage. Clicking on a stage that is currently selected does nothing.

# Main Menu
The main menu lists all the different pages that can be found in the program. Each item in the menu can be clicked to switch to that page. The keyboard shortcut listed to the right of the menu item's name will also trigger a switch to that page. When a page is being currently viewed, it is highlighted. Clicking on a page that is already being viewed does nothing.

# Stage List
The screen is filled with a table of all the existing stages. The stages are listed in their order, with the oldest stage at the top.

Clicking the Add button will add a stage AFTER the row where the button was clicked. For example, if the button was clicked on Row 2, the new stage will be added in Slot 3. The default name of a new stage is a "Blank", with the abbreivation B. If there is another stage with that name, a 1 is appended to the end.

Clicking and holding the icon on the left side of the row allows users to reoreder stages by dragging them up or down.

Clicking anywhere else on the stage's row will open the Stage Information page.

## Stage Information 
The stage's name and abbreviation can be edited at the top of the page by clicking on the relevant section and typing.

Users can switch between Pronounciation, Allophony and Orthography by clicking on the tags. Clicking on a currently selected tag does not do anything.

## Regex Editor
The regex table shows different regex rules, ordered with the oldest at the top. The tag on the far left side of the table rows shows which stage that regex rule originates from. Clicking into the row and typing will allow that regex rule to be updated.

Clicking the Add button will add a regex rule AFTER the row where the button was clicked. For example, if the button was clicked on Row 2, the new rule will be added in Slot 3. A new regex rule has no regex in the field.

Regex rules from stages older than the current one cannot be edited in any way. Regex rules from the current or future stages can be reordered by dragging the icon found on the left side.

The sample word allows users to type a word in the top box. The sample result box in every row will display what the sample word looks like after applying that rule and all the rules before it.


# Sound Changes
The sound change table shows different sound changes, ordered with the oldest at the top. Each row shows the name of the Sound Change and Internal Notes for that Sound Change.

Clicking the Add button will add a sound change AFTER the row where the button was clicked. For example, if the button was clicked on Row 2, the new change will be added in Slot 3. 

Sound changes can be reordered by dragging the draggable icon in each row.

The sample word allows users to type a word in the top box. The sample result box in every row will display what the sample word looks like after applying that sound change and all the rules before it.

Clicking on row or add button will open the Edit Sound Change Modal.

## Sound Change Page

The Sound Change's name can be edited by clicking on it and typing.

For a new Sound Change, the unlock slider is set to unlocked and cannot be changed. For an existing Sound Change, the unlock slider is set to locked. Attempting to toggle the slider from Locked to Unlocked will open a dialog, asking if the user s certain they want to edit the Sound Change.

The top of the Sound Change Page has the following fields:
- Chapter Name (Text Field, default empty)
- Recursion (Checkbox, default unchecked)
- Odds (Slider 0 to 100, default 100)
- Prose (Text Field)
- Interal Notes (Text Field)

The bottom of the Sound Change page uses the same Regex Editor as Stage Information.

# Morphology

The top of each morphology page shows checkboxes for each gender, case and plurality inflection. Checking this box will impact all of morpohologies for this type of this stage.

Existing Morphologies for the stage are listed below in a grid. Clicking on an exisitng Morphology or the Add button in the top right will open the edit Morpohology page.

## Edit Morphology (Noun)

Clicking the Morphology Name or the Abbreviation will allow the user to edit the field by typing.

For Morphologies that require a gender, a dropdown is shown in the header to specificy. Selecting a gender will gray out those genders' columns in the morphology table.

For Morphologies that require reference to another Noun, the search box allows users to search the name of another noun morpohology.

The bottom half of the Morphology page shows the table for that specific morpohology. Cases are represented rows, and different inflections in columns. If the current stage does not inflect for a specific quanity or gender, those columns in the table are greyed out.

The toggle switches at the top of the Morpohology page control the content of the table.

Clicking into each cell will allow the user to type the regex rule that be applied for that inflection. Pressing Enter or clicking outside of the table will save that inflection.

## Override Mode
If the current morphology inheirits from elsewhere, the override toggle is shown in the top right. The default state is toggled off.

When the toggle is off, the morphology table is filled in with inheirited rules. Clicking into the table does not allow for edits. When the toggle is on, the morphology table shows the override rules for this stage and morphology.

## Preview Mode
The preview toggle is shown in the top right. The default state is off.

When the toggle is off, the morphology table behaves as normal. When the toggle is on, the Sample Word box appears in the top right and the morphology table is cleared. When a query is typed into the Sample Word Box, each cell in the morphology table updates to show that query transformed by the regex rule for that inflection.

When the toggle is on, the morphology table cannot be edited.

# Lexicon
