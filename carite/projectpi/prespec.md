# Project Π pre-spec

# **Context**

I’ve been working on a constructed language with a friend for almost a decade at this point. We specialize in a subniche of the hobby of constructing languages (conlanging, which is a niche on its own already) that revolves around alternate histories and deriving a new language from a real one through scientific means, i.e. adhering to the science regarding language evolution we know so that it hypothetically could have existed today.  
   
Throughout our work, I’ve assembled a handful of “tools” to aid us in keeping track of this massive database of data. This has resulted in an automatically generated site on GitHub ([https://bass	oonian.github.io/carite/](https://bassoonian.github.io/carite/)) that is… quite literally a single Google spreadsheet parsed by JavaScript. This makes it quite a hassle to work with, so we’ve been hoping to make something with an actual UI for a while now.  
   
I’ve been trying out differe	t UI libraries in Python throughout the last few years (the project has also kind of been on hold for this period because both my language partner and I have been very busy with life) and I’ve kept bumping into issues with UI design (and the coding part, but that’s outside of your scope). As such, we would love to have you help us spec out the actual user interface part (both a rough mockup of positioning of text fields and the like but also helping brainstorm with how to access what). I’ll do my best to explain what precisely we’re in need of – if anything is unclear, please don’t hesitate to get in touch and I’d be happy to elaborate.  
   
There is a decent enough chance that throughout using the product, we’ll find shortcomings in the actual functionality, so I hope you’d be game to help adjust bits and pieces over time as necessary :)

# **Glossary**

Consider this a bit of a glossary in which I’ll explain some concepts core to understanding the way of thinking.  
   
We work on a single language but divided into **stages**. Compare this to Old English, Middle English, Modern English etc. Stages are technically somewhat arbitrary divisions (with names), but key to help keep an overview of what we’re doing. Editing any part of the language only relates to that particular stage (e.g. you’d add a new dictionary entry for Old English), but that stage needs to be able to interact with following stages (so that said Old English word can be inherited and evolve into a newer form). This means that in the “general sidebar”, or whatever you’d like to make of it, there needs to be an easily accessible way to switch between stages.  
   
The very first stage (say, ID 0\) is the original, purely scientific stage that doesn’t matter for us. As such, it’ll behave slightly differently compared to all stages that follow it, but it’s simply a matter of just disabling a handful of features, so you don’t need to worry about this overly much.

# **The editors**

## **Information**

This is basically a relatively straightforward text edit bit, divided into different categories. It sets the general information of a stage:  
- Nomenclature  
  - Full name (e.g. Old English)  
  - Abbreviation (e.g. OE)  
- Pronunciation  
- Allophony  
- Orthography  
   
Nomenclature are just very simplistic text fields, the other three are slightly more complex. Think of them as longer text fields that allow for multiple lines that basically enable you to define regex rules. For total clarity, though it probably doesn’t matter super much:  
- Pronunciation consists of any additional rules that need to be applied to the raw word data to produce the International Phonetic Alphabet pronunciation. Think of e.g. “bard” in non-rhotic English dialects having to lose the r and change \+ lengthen the vowel to get /bɑːd/.  
- Allophony works the same way, but it has to do with specific extra changes that are entirely conditional and predictable. These tend to be harder to understand for non-linguists, but you’ll notice that e.g. between “pot” and “spot”, you’ll notice a puff of air coming out of your mouth if you say the former, but not the latter.  
- Orthography basically consists of rules that need to be applied to the raw word data to produce the spelling. Think of e.g. “kw” needing to be parsed and displayed as “qu”.  
   
I’ve toyed around with multiple ways to deal with this in the past. The cleanest one is probably having a whole bunch of individual text fields side by side, e.g. something I did in the past for orthography:  
   
Because regex is obviously order-bound, there needs to be an easy way for these three regex “pages” for changes to be reordered and swapped around (preferably with more freedom than my old “insert after this” button). A way to test the regex on that specific page (with a simple input and output) would also be very helpful (to make sure that the pronunciation regex produces the correct results, for example).  
 

## **Sound Changes**

One of the primary ways languages evolve over time is through **sound changes**. I’ll elaborate on this more when we get to the spec of said editor, but you can basically look at this at a massive regex machine, with the sound changes being the regex rules that get applied to things from a previous stage to result in the things of the current stage. For this obvious reason, stage 0 does not need sound changes enabled (because it has nothing to apply them to).  
   
As before, since regex rules produce different results based on the order, the order of these is key, and being able to conveniently reorder would be extremely helpful.  
   
Sound changes consist of the following data:  
- The actual regex rules  
- Prose  
- The name of a chapter if it starts one (optional)  
- Internal notes  
- Recursion  
- Odds  
- Behind the scenes  
   
The actual regex rules are pretty much identical to how the pronunciation regex (see above) is laid out. Here, too, a convenient field to test the regex would be welcome, as well as potentially a second field to test all sound changes *up to that point*, i.e. if you’d give an input while checking/editing the fourth change, giving input to the second field would have it undergo all regex rules of the first up to and including the fourth change.  
   
Prose is basically a large text field that “officially” describes the change that happens. This is more of a coding thing than necessarily something you need to care about, but lay-out options like bold, italics and (later) embedding actual dictionary entries so they get included automatically are important here.  
   
Like how a book is structured, sometimes sound changes need to start a new chapter. I’ve traditionally just had an optional text field that can be left empty if unused, but feel free to suggest better solutions for this.  
   
Internal notes are quite literally what it says – a place for internal notes that export quite simply ignores.  
   
Recursion is a checkbox and basically means “continue applying this change’s regex rules until the output no longer changes”.  
   
Odds are 100% by default, and this remains in most cases, but sometimes a change is only allowed to affect a specific percentage of words that qualify. This could be a raw value field, but perhaps also a slider?  
Behind the scenes is also a checkbox that basically prevents it from being exported into public documents. Think of “behind the scenes” shuffling of raw values that don’t need to be mentioned explicitly to any reader.  
   
Because sound changes will dictate everything that happens (and editing the first sound change of the first real stage (i.e. not 0\) will possibly affect the output of anything in any following sound change *and* stage, I think it’s highly recommended to have sound change fields “locked” and disabled by default so they can be viewed and explored without the risk of accidentally setting everything on fire.  
   
I’ve toyed around with dropdown menus and sliders (and both) to navigate between different sound changes (all within the same stage of course), but as always everything is open for discussion.

## **Morphology**

Oh boy, this is a big one. Morphology is basically the non-syntactic grammar of languages. English is quite tame here, but e.g. plurals and verbal conjugation belong here. This gets big fast, so I’ll split it as necessary.  
   
Worth noting is that brand new morphology entries in any of the categories below can only be made in the very first stage – in all other cases, entries are strictly inherited.

### **Nominal**

Nominal morphology is more straightforward than verbal morphology, but to make up of it, it consists of three subgroups, i.e. nouns, pronouns and adjectives. Nouns and pronouns are very similar in how they need to behave in the interface, and adjectives are luckily trivial. It very likely makes sense to group noun/pronoun morphology in the same bit, while adjective morphology is separate.  
   
Per-stage information that’s important is which number and genders nominal morphology inflects for. On top of that, there’s also case, which is different for nouns and pronouns, so this would need to be separate.  
   
Noun and pronoun morphology entries consist of a name, an abbreviation, and in the case of nouns, a gender (from the list specified above). There is also a table for number (columns) and case (rows) that needs to be filled out if brand new or is read-only if inherited. If inherited, however, there needs to be a second table where overrides can be made.  
   
Adjective morphology entries are luckily far simpler: they consist of a name, an abbreviation, and a referenced noun/pronoun inflection for each gender that the stage needs to inflect for.

### **Verbal**

Verbs are more straightforward, without subcategories, but in return, they’re a mess. Per-stage information includes which number and which amount of persons they decline for (traditionally 2 numbers and 3 persons), and this table basically gets multiplied for each TAM included (to keep this simple enough, consider TAM to be an English tense), which in turn gets multiplied by the amount of voices (active vs passive vs middle, which will also differ across stages). On top of this, there can be extra fields, such as infinitives and participles.  
   
To keep it sane for both you and us, and because not all combinations of TAM get used, I suggest that per-stage, you can add a “table number” for each number/person table which consists of three dropdown menus: one for voice, one for mood, and one for tense/aspect.  
   
Worth noting is that the participles also inflect like adjectives, so all the extra fields need to have the possibility to be assigned an adjective morphology category.  
   
Problems for future us, but verbal morphology is prone to restructuring, so when stage 1 goes to stage 2 and what used to be the future is now suddenly something else (but with the exact same data), we should find a straightforward way to help these continue to be linked. This is technically also a possibility for nouns, but just less likely so.

## **Lexicon**

Lexicon is basically a fancy word for dictionary, or vocabulary, or whatever you prefer. In short: all the words. This is going to be a tricky section to navigate, both in terms of design and in terms of how it works mechanically. I think it’s very important to have a clear list of all lexicon entries with filters and a search bar, that’s for sure. I’ll subdivide this category a bit to hopefully keep things somewhat clear.

### **Primary parameters**

A lexicon entry, i.e. a word, always has the following information:  
- Raw form  
- Raw form override  
- Meanings  
- Part of speech  
- Inflection pattern  
- Internal notes  
- Prose  
- Sources  
   
The raw form is raw data that undergoes the phonology, allophony and orthography rules outlined before. It is also exposed to sound changes for any stage that follows it (if it gets inherited, that is). The override is empty by default but allows you to change the raw form if preferred. The raw form field is always read-only.  
   
Meanings are basically the translations. This is essentially an array of possible translations, but it’s important that more than just a meaning can be given. For example, occurrence may also want to be specified (informal, formal, archaic, dialectal), as well as which case adpositions/verbs take, and other information such as euphemistic and idiomatic usage. This varies between possible meanings of a single word, so if a single word both means “tree” and “river”, for whatever reason, they need to have individual options.  
   
Words always belong to a part of speech class. The following exist:  
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
   
Inflection patterns refer to which inflection pattern a word belongs to, as described above.  
   
Internal notes are obvious, prose is basically what follows in a dictionary after the rough description.  
   
Sources (see also at the bottom of this document) basically lists all sources of the project. For each entry individually, you can specify if a source is relevant or not and, if so, on which pages.

### **Word origin**

A word can be one out of four possible sources: inheritance, derivation, loan, and ex-nihilo. The vast majority statistically will consist of inheritance and derivation, but the other two are also important. Because this is extremely integral to a word, this cannot be changed once a word exists and needs to be selected before adding a new lexicon entry.  
   
Non-inheritances will have an additional components field, which is required for derivations and optional for loans. This refers to the morphemes that make up a word.  
   
Ex nihilo words will feature an additional checkbox about whether they’re scientifically sourced. Most ex-nihilo words do in fact have a scientific basis, but there are a few ex-nihilo words that have been named after people supporting the project, in which case they are exempt from sourcing (the sourcing part will be disabled) and will be clearly marked as such when exported.


### **Interaction with sporadic sound changes**

If a word has undergone a sporadic sound change, the outcome of this can be toggled with a checkbox. This obviously means that this part of the editing menu will be of dynamic size (height, most likely).

## **Corpus**

What is a language without texts, after all\! This bit is still tentative in form, because I never got this far when it comes to interfacing. The premise is simple, however: a list of texts (with the obvious possibility of adding and deleting them) that consist of references and instructions to all the previous data, inflecting words correctly as specified in the data. Perhaps something with literally Duolingo-esque building blocks that can be reordered and double clicked to open a modal where you can specify what the building block fetches from alongside a real-time render so you can see how it looks?

# **Also important**

## **Sources**

Due to the (wannabe) scientific nature of this project, academic sourcing is super important. This means there needs to be a centralized place to register sources, which can then be tracked and referenced as outlined above. Key to each source is the following:  
- Name  
- Author(s)  
- Year of publication  
- Reference (e.g. Adiego 2016a) \[this can probably be automated, though\]  
   
We originally also tracked links to Google Books and WorldCat, but this is just a guise for not just using the pdfs ourselves, so we should probably just leave that for what it is.  
   
It’s also important to clearly show whether a source is referenced throughout the project or not. Perhaps the list can also include the number of references made, and if it’s a table we’ll probably want to be able to sort the table by the different fields. A search bar would also be useful here.

## **Export**

This is luckily only superficial for you, but there also needs to be a way to export everything into a format that readers can digest. In short: a (global) export page (the same way sources also span all stages at once) with buttons to export for web and to LaTeX. I imagine these will take a while to happen, so a log so you can see the conversion is currently in progress would be extremely welcome here too (and the log field can be shared between different export targets, no real need to distinguish there since you can only export one at a time anyway).

# **Free real estate**

Below are some musings on stuff that would be super cool to have, but for which I have no idea where to best integrate them.

## **Statistics**

These can be project-wide statistics (i.e. spanning all stages), but also per-stage. A tracker for how many hours I’ve wasted with the file open, for example, but also perhaps the amount of website visits etc. Within stages, it’d be useful to have pie charts regarding the distribution of sounds, inflection patterns, word origins etc. Due to how vague this is, I’m not asking for an actual design for the statistics pages, but rather for your thoughts on where to plug the buttons.

## **To-do list**

This can be both local and global. Basically a list that shows what still needs to be done in terms of sourcing, i.e. which lexicon entries haven’t been checked in a source.

## **Warning list**

This could be merged or consolidated with the list above. Sometimes, specific conditions should give warnings, e.g. adding a new case without completing the forms of said case in the inflection tables.

## **Other pages**

If you check the website linked at the top of this pre-spec (which needs an overhaul anyway, you’ll notice that as part of the documentation, there’s extra pages such as an introduction and the anthropology category. It’d obviously be beneficial to also have this centralized rather than having to do this outside of the editor for each export individually, but I have *no* clue where or how to place this. Thoughts are very welcome.
