# ROUND THREE

> I understand that sound changes have odds from 0% to 100%. When does this RNG get rolled?

> **Update**: Looking at the previous screenshots, what explcit improvements are you expecting from my overhaul? I've seeded the following examples, but I'm looking to more specific ones to you and your project. Having these desires from you will drastically change how I design this. Another way to think of this is "In what measurable ways will psf's interface better than Jasper's existing interface?"

> What is the difference between the "other pages" documentation and the "corpus"?

> Can I see or use the alpha / beta versions of the software?

# ROUND TWO
> Looking at the previous screenshots, what explcit improvements are you expecting from my overhaul? I've seeded the following examples, but I'm looking to more specific ones to you and your project. 

I want:
- high traffic flows to be easier to use.
- a consistent intended usage pattern enforced by design
- the software to be prettier to use
- to make it easier for new people to our hobby to use this generation
- to empower power users to perform common tasks

> Can I please see the existing Google Sheet that is used to generate the website?

https://docs.google.com/spreadsheets/d/1ujWrd-kgZ3LMU7G71FWactoF4ihVIwr7YMxZgqg4Hns/edit?gid=284553596#gid=284553596

> For lexicon, do we look at the different inflection patterns established for nouns? Do we only look at patterns that are valid for this stage?

only for this stage, but lexicon is wider than nouns - it also includes indeclinables (such as prepositions and adverbs), as well as other declinables such as adjectives and verbs

> Is prose like "use this in a sentence"?

it's basically just "extra fluff for documentation", generally regarding etymology and usage

> Is a "sporadic sound change" the same as "sound changes" from above?

sporadic sound changes are sound changes with odds < 100%
(which in the world of linguistics are very uncommon)

# ROUND ONE
> Is there a maximum number of rules?

no

> Does this UI need to considered touch inputs? What is the most likely device / screen this UI will be rendered on?

only ever on a laptop, so no need to worry about varying resolutions, horizontal vs vertical etc

> When previewing changes, is there a common word that can be used in all cases? If not, does the preview word need to be definable?

ideally this would just be a text field I think, since it may be useful to specifically test edge cases

> I do not understand Chapter Name in relationship to Sound Changes. Could you explin in another way?

it may be a bit of a hacky idea, but the original function of this was that multiple sound changes can be grouped in a single "chapter" for documentation purposes, and this field would just mean that said sound change starts a new chapter (no point in assigning sound changes to chapters because there's no filtering or reordering anyway)

> Will users expect markdown, richtext, or plaintext for their input fields?

plaintext for the overwhelming majority, though the documentation fields with actual text may be the nicest in markdown (also thinking from a coding perspective to have exporting possibilities to html, but also latex etc)

> Should sound changes be high friction? Instead of locking the fields by default, can the program just aggressively log all actions for easy undo?

I wonder if this wouldn't have any massive repercussions regarding performance. the truth is that sound changes are so extremely influential on every other editor and database (since everything is aggressively put through the regex chain) that I'd personally be wary of "re-regexing" the entire database too often. it's the sort of stuff that you ideally never touch again except for "bugfixes" once it's in place, because it can really fuck up everything else or require refactors

> Can a stage have multiple sound changes?

absolutely, they can easily have about 50

> Can a sound change have multiple regex rules?

yes

> If yes, does every regex rule need prose / chapter / internal notes

no, one per sound change suffices

> Can you explain adjective morphology? Are you referencing a previously entered noun / pronoun? What is inflection?

inflection is basically how words "change" depending on the context. this can be as simple as singular vs plural -s, or how verbs get -ed in the past, but outside of English can get more tricky with cases (German may be the easiest reference here, or alternatively Latin etc, the tldr is that words can change form depending on their function within a sentence). adjectives also inflect for gender (think Spanish -o vs -a), so linking them to the noun tables (eg Spanish -o/-os and -a/-as) would be the most straightforward

> What is a participle? Does each VERB need to be able to be assigned to an adjective?

English's participles are the past participle -ed (eg "he is wanted" or "he has wanted") and the present participle -ing (eg "he is walking" or "the walking man"). not each verb needs to be assigned to an adjective, but rather each verb _inflection_ needs to have its participles linked to an adjective inflection table (think of uh Spanish -ar vs -er vs -ir as different inflection tables)
